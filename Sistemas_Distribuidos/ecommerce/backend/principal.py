import ast
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import json 
import pika
from pika.exchange_type import ExchangeType
from pydantic import BaseModel
import requests

from dotenv import dotenv_values

# RabbitMQ 
params = pika.ConnectionParameters('localhost', heartbeat=720)
connection = pika.BlockingConnection(params)
channel = connection.channel()

def pikaConnect(exchanges):

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Declara todas as exchanges por ser primeiro a ser iniciado
    for exchange in exchanges.keys():
        channel.exchange_declare( exchange=exchange, 
                        exchange_type=ExchangeType.topic )

    # Consome as exchanges Pagamentos* e Pedidos_Enviados
    for exchange, r_key in list(iter(exchanges.items()))[2:]:

        q = channel.queue_declare(
                queue='Principal/' + exchange,
                exclusive=False )

        channel.queue_bind(exchange=exchange, 
                           queue=q.method.queue, 
                           routing_key=r_key)

        channel.basic_consume(queue=q.method.queue, 
                              auto_ack=True, 
                              on_message_callback=consume)

    print("[MS]PRINCIPAL -> Inicializado.")
    channel.start_consuming()

def consume(ch, method, properties, body):

    m = json.dumps(body.decode("utf-8"))
    m = m.replace("false", "False")
    m = m.replace("null", "None")
    m = m.replace("true", "True")
    message = json.loads(m)

    message = ast.literal_eval(message)

    print(f"[MS]PRINCIPAL -> MESSAGE: {str(message)}")

    if "status" in message.keys():
        if message["status"] == 'Recusado':

            channel .basic_publish(
                exchange = "Pedidos_Excluidos",
                routing_key=f"Pedido.{message['id']}.Excluido",
                body = str(lastOrder) )
    return

# FastAPI init
app = FastAPI()

# Middleware de qualquer localhost:*
origins = [ "http://localhost", "http://127.0.0.1", ]  
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"{origin}:{port}" 
                   for origin in origins 
                   for port in range(3000, 3333)],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic para receber requests de pedido
class Item(BaseModel):
    produto: dict
    quantidade: int
    preco: float

class Order(BaseModel):
    id: int
    items: list[Item]
    quantidade: int
    total: float
    status: str

# Principal -> Database
@app.post("/pedido")
async def realizar_pedido(pedido: Order):

    pedido = pedido.model_dump()

    print( f"[MS]PRINCIPAL -> Pedido {pedido['id']}: " +
           f"R${pedido['total']}" )

    global lastOrder
    lastOrder = pedido

    if not connection or connection.is_closed:
        pikaConnect()

    if pedido['status'] == "Criado":
        e = "Pedidos_Criados"
        r_key = f"Pedido.{pedido['id']}.Criado"

    if pedido['status'] == "Excluido":
        e = "Pedidos_Excluidos"
        r_key = f"Pedido.{pedido['id']}.Excluido"

    channel.basic_publish(
            exchange = e,
            routing_key=r_key,
            body = str(pedido) )

    return { "Pedido" : pedido['id'],
             "Status" : pedido['status'] }

# Request de produtos para o MS Estoque
# Principal -> Estoque -> Database
@app.get("/produtos")
async def get_produtos( skip: int = 1,
                        limit: int = 12 ):

    env_vars = dotenv_values("../.env")
    estoque_port = env_vars.get("estoquePORT")
    url = f"http://localhost:{estoque_port}/produtos?skip={skip}&limit={limit}"
    print("[MS]PRINCIPAL -> Request:", url)
    produtos = requests.get(url).json()

    return produtos

if __name__ == "__main__":

    # Exchanges do servico principal
    exchanges = {
        'Pedidos_Criados' : 'Pedido.#.Criado',
        'Pedidos_Excluidos' : 'Pedido.#.Excluido',
        'Pagamentos_Aprovados' : 'Pagamento.#.Aprovado',
        'Pagamentos_Recusados' : 'Pagamento.#.Recusado',
        'Pedidos_Enviados' : 'Pedido.#.Enviado'
    }

    pikaConnect(exchanges)
