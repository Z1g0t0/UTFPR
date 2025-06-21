## Requisitos:

### Node.js

Projeto foi desenvolvido com Node.js 20.16.0

### Python

Projeto foi desenvolvido com Python 3.13.1

### Docker

Para execucao das imagens rabbitmq stripe-cli
As imagens serao instaladas pelo `init.sh`

### Stripe Keys

Chaves pk e sk adquiridas criando uma conta em https//stripe.com/
Adiciona-las no arquivo .env correspondente

    STRIPE_API_KEY="pk_test_(...)"
    STRIPE_SECRET_KEY="sk_test_(...)"

## Configuracao

Em ./backend, recomenda-se criar uma venv

    python3 -m venv .

E instalar as bibliotecas necessarias com:

    ./bin/python -m pip install -r requirements.txt
Ou
    
    ./Scripts/python -m pip install -r requirements.txt
    
Em ./frontend, instalar as bibliotecas necessarias com:

    npm install

Atribuir direitos de execucao ao arquivo `init.sh` com:

    chmod +x init.sh

Ao executar pela primeira vez gera-se produtos usando a biblioteca Faker, o numero de produtos gerados pode ser especificados na primeira linha do arquivo `init.sh`. Por padrao gera-se 111 produtos

Por causa dos comandos docker entre outros executar com sudo: 

    sudo ./init.sh

E acessar o localhost/{port} retornada pelo Next.js e localhost/{port}/sse para verificar as notificacoes sse.

Cartoes de teste Stripe:
    
Pagamento aprovado: 4242 4242 4242 4242
Pagamento recusado: 4000 0000 0000 0002
