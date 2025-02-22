#!/bin/bash

# Caso primeira vez executando, numero de produtos a ser gerado
produtos=111

# Update das imagens se necessario
echo "Atualizando imagens docker..."
docker pull rabbitmq:4.0-management
docker pull stripe/stripe-cli:latest

# Animacao de carregamento
pid=0
symbols='-\|/'
i=0
spin() {
	while kill -0 $pid 2>/dev/null
	do
		i=$(( (i+1) %4 ))
		printf "\r[${symbols:$i:1}]"
		sleep .1
	done
	printf "\r"
}
spin &

# Funcao para criar/atualizar variaveis em .env
env_var_handler() {
    local var="$1"
    local value="$2"
    
    if grep -q "^$var=" .env; then
        current_value=$(grep "^$var=" .env | cut -d '=' -f2)
        
        if [ "$current_value" != "$value" ]; then
            sed -i "s/^$var=.*/$var=$value/" .env
            echo "$var atualizado no .env"
        else
            echo "$var nao mudou, mantendo o valor atual no .env"
        fi
    else
        echo "$var=$value" >> .env
        echo "$var adicionado ao .env"
    fi
}

port_handler() {
	port=$1
	while ss -tuln | grep ":$port" &>/dev/null; do
		((port++))
		sleep 1
	done

	echo "$port"
}

# Funcao para remover containers dockers pelo nome
dockerRM() {
	echo "Removendo containers docker: $1"
	CONTAINER_ID=$(docker ps -a | grep $1 | awk '{print $1}')
	docker stop $CONTAINER_ID 2>&1 &
	sleep 4
	docker rm $CONTAINER_ID 2>&1 &
	sleep 4
}


# === VARIAVEIS ENV ===
# Verifica se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "Arquivo .env nao encontrado."
    exit 1
fi

# Mantem apenas STRIPE_API_KEY/STRIPE_SECRET_KEY em .env
grep -E '^(STRIPE_API_KEY|STRIPE_SECRET_KEY)=' .env > .env.tmp && mv .env.tmp .env

source .env

# Verifica se stripe keys foram carregadas e nao estao vazias
if [ -z "$STRIPE_API_KEY" ] || [ -z "$STRIPE_SECRET_KEY" ]; then
    echo "STRIPE_API_KEY ou STRIPE_SECRET_KEY nao configurado em .env"
    exit 1
fi

# === || ===

# === RABBITMQ (DOCKER) ===
dockerRM rabbitmq
sudo docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management
sleep 12
# === || ===

# === BACKEND ===
echo "Inicializando backend..."

pkill -9 python
pkill -9 uvicorn 

# Ativa o ambiente virtual caso necessario
if [ -d "./backend/bin" ]; then
	echo "Ativando ambiente virtual..."
	. ./backend/bin/activate
else
	echo "Ambiente virtual nao encontrado."
	exit 1
fi

# Verifica se ha ecommerce.db e se nao executa generate_products.py
if [ ! -f "./backend/ecommerce.db" ]; then
	cd backend
  	echo "ecommerce.db nao foi encontrado, gerando $produtos produtos..."
	python ./generate_products.py $produtos
	cd ..
fi

sleep 3

# Inicializacao do microservico de pagamento em conjunto
# com o webhook do Stripe CLI 
echo "Inicializando Stripe CLI..."
source .env

echo "STRIPE_API_KEY: $STRIPE_API_KEY"
echo "STRIPE_SECRET_KEY: $STRIPE_SECRET_KEY"

dockerRM stripe

STRIPE_WEBHOOK_SECRET=$(docker run stripe/stripe-cli listen --print-secret --api-key $STRIPE_SECRET_KEY)

sleep 4

if [ -z "$STRIPE_WEBHOOK_SECRET" ]; then
    echo "Falha ao adquirir STRIPE_WEBHOOK_SECRET"
    exit 1
else
    echo "STRIPE_WEBHOOK_SECRET: $STRIPE_WEBHOOK_SECRET"
fi

env_var_handler "STRIPE_WEBHOOK_SECRET" "$STRIPE_WEBHOOK_SECRET"

sleep 3

env_var_handler "pagamentoPORT" $(port_handler 8000)

source .env

docker run -i -d --network="host" stripe/stripe-cli listen --forward-to http://localhost:$pagamentoPORT/stripe-webhook --api-key $STRIPE_SECRET_KEY

sleep 3
cd backend
uvicorn "pagamento:app" --port $pagamentoPORT &
sleep 3
python "pagamento.py" &
cd ..
# === || ===

# Restante das API's
sleep 3
mss=("principal" "estoque" "notificacao")

for name in "${mss[@]}"; do

	cd backend

	port=$(port_handler 8000)

	uvicorn "${name}:app" --port "$port" &
	sleep 3
	python "${name}.py" &

	echo "PORT ${name}: $port"

	cd ..
    env_var_handler "${name}PORT" "$port"
	
	sleep 3
	#read -n 1 -p Continue?;

done

python ./backend/entrega.py &

# Adiciona propriedade public para o port do microservico de 
# Notificacao para ser usado no frontend
source .env
env_var_handler "NEXT_PUBLIC_notificacaoPORT" $notificacaoPORT
# === || ===


# === FRONTEND ===
echo "Inicializando frontend..."
cp .env ./frontend/.env.local

pkill -9 node

cd ./frontend
sudo npm run dev
# === || ===
