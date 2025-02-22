import pika

import ast
import json

# RabbitMQ 
params = pika.ConnectionParameters('localhost', heartbeat=720)
connection = pika.BlockingConnection(params)
channel = connection.channel()

def pikaConnect():

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Consome as exchanges Pagamentos* e Pedidos_Enviados

    q = channel.queue_declare(
            queue='Entrega/' + 'Pagamentos_Aprovados',
            exclusive=False )

    channel.queue_bind(exchange='Pagamentos_Aprovados', 
                       queue=q.method.queue, 
                       routing_key='Pagamento.#.Aprovado')

    channel.basic_consume(queue=q.method.queue, 
                          auto_ack=True, 
                          on_message_callback=consume)

    print("[MS]ENTREGA -> Inicializado.")
    channel.start_consuming()

def consume(ch, method, properties, body):

    m = json.dumps(body.decode("utf-8"))
    m = m.replace("false", "False")
    m = m.replace("null", "None")
    m = m.replace("true", "True")
    message = json.loads(m)

    message = ast.literal_eval(message)

    amount = message['amount']
    print(f"[MS]ENTREGA - > Enviando pedido de valor: {amount}")
    channel.basic_publish(exchange='Pedidos_Enviados', 
            routing_key=f"Pedido.Valor_{amount}.Enviado",
            body=str(message))

if __name__ == "__main__":

    # Exchanges do servico de entrega
    pikaConnect()
