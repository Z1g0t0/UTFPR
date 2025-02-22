import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

import pika
import requests

from collections import deque
from pydantic import BaseModel

from dotenv import dotenv_values

# RabbitMQ 
params = pika.ConnectionParameters('localhost', heartbeat=720)
connection = pika.BlockingConnection(params)
channel = connection.channel()

def pikaConnect(exchanges):

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    for exchange, r_key in list(iter(exchanges.items())):

        q = channel.queue_declare(
                queue='Notificacao/' + exchange,
                exclusive=False )

        channel.queue_bind(exchange=exchange, 
                           queue=q.method.queue, 
                           routing_key=r_key)

        channel.basic_consume(queue=q.method.queue, 
                              auto_ack=True, 
                              on_message_callback=consume)

    print("[MS]NOTIFICACAO -> Inicializado.")
    channel.start_consuming()


app = FastAPI()
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

def consume(ch, method, properties, body):
  
    env_vars = dotenv_values("../.env")
    notificacaoPORT = env_vars.get("notificacaoPORT")
    url = f"http://localhost:{notificacaoPORT}/notify"

    message = body.decode("utf-8")
    msg = { 'Tipo': str(method.routing_key), 'Mensagem': message }

    key = (method.routing_key.split("."))

    print(f"[MS]NOTIFICACAO -> Evento: {str(key)}")
    
    try:
        requests.post(url=url, json=msg)

    except Exception as e:
        print("NOTIFICACAO ERROR: " + str(e))

    return

class EventModel(BaseModel):
    Tipo : str
    Mensagem: str

class SSEEvent:
    EVENTS = deque()
    
    @staticmethod
    def add_event(event: EventModel):
        SSEEvent.EVENTS.append(event)

    @staticmethod
    def get_event():
        
        if len(SSEEvent.EVENTS) > 0:
            return SSEEvent.EVENTS.popleft()
        else:
            return None
    
    @staticmethod
    def count():
        return len(SSEEvent.EVENTS)

@app.post("/notify")
async def new_event(event: EventModel):
    #print(f"[MS]NOTIFICACAO -> Evento[{SSEEvent.count()}]: {event.Mensagem}")

    SSEEvent.add_event(event)
    return { "Message" : event.Mensagem,
             "Count" : SSEEvent.count() }

@app.get("/stream")
async def stream_events(req: Request):
    async def stream_generator():
        while True:
            if await req.is_disconnected():
                print("[MS]NOTIFICACAO -> SSE desconectado")
                break
            event = SSEEvent.get_event()
            if event:
                yield "Event: {}".format(event.model_dump_json())
            await asyncio.sleep(1)

    return EventSourceResponse(stream_generator())

if __name__ == "__main__":

    exchanges = {
        'Pedidos_Criados' : 'Pedido.#.Criado',
        'Pedidos_Excluidos' : 'Pedido.#.Excluido',
        'Pagamentos_Aprovados' : 'Pagamento.#.Aprovado',
        'Pagamentos_Recusados' : 'Pagamento.#.Recusado',
        'Pedidos_Enviados' : 'Pedido.#.Enviado'
    }

    padrao = EventModel(
        Tipo="Inicializacao", 
        Mensagem="Notificacao SSE Inicializado" )

    pikaConnect(exchanges)


