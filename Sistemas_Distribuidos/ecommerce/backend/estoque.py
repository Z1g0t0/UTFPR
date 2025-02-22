import database

import ast
from fastapi import FastAPI, Depends
import json
import pika
from sqlalchemy.orm import Session
import sqlite3
from typing import Annotated

# RabbitMQ 
params = pika.ConnectionParameters('localhost', heartbeat=720)
connection = pika.BlockingConnection(params)
channel = connection.channel()

def pikaConnect(exchanges):

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    for exchange, r_key in list(iter(exchanges.items())):

        q = channel.queue_declare(
                queue='Estoque/' + exchange,
                exclusive=False )

        channel.queue_bind(exchange=exchange, 
                           queue=q.method.queue, 
                           routing_key=r_key)

        channel.basic_consume(queue=q.method.queue, 
                              auto_ack=True, 
                              on_message_callback=consume)

    print("[MS]ESTOQUE -> Inicializado.")
    channel.start_consuming()

# Database init
def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()
db_dependency = Annotated[Session, Depends(get_db)]
database.Base.metadata.create_all(bind=database.engine)

# FastAPI 
app = FastAPI()

# Estoque -> Database
@app.get("/produtos")
async def get_produtos( db: db_dependency, 
                        skip: int = 1,
                        limit: int = 12 ):

    #skip = (page*limit)-1
    produtos = db.query(database.Produto).offset(skip).limit(limit).all()
    return produtos 


def consume(ch, method, properties, body):

    m = json.dumps(body.decode("utf-8"))
    m = m.replace("false", "False")
    m = m.replace("null", "None")
    m = m.replace("true", "True")
    message = json.loads(m)

    message = ast.literal_eval(message)
    items = message['items']

    # Verifica se o pedido foi criado ou excluido
    key = (method.routing_key.split("."))[-1]

    print(f"[MS]ESTOQUE -> {key}")

    # Query do estoque atual de cada produto e atualiza
    for item in items:
        
        id = item['produto']['id']
        quantity = item['quantidade']

        #Verifica se de fato o estoque eh o mesmo
        res = sql_exe(""" SELECT id, estoque
                          FROM produtos
                          WHERE id = ? """, [id])

        supply = res[0][1]

        if key == 'Criado':
            estoque = supply - quantity
        elif key == 'Excluido':
            estoque = supply + quantity

        if estoque < 0:
            print("[MS]ESTOQUE -> Pedido superior ao estoque. Cancelando.")
            continue

        print(f"""[MS]ESTOQUE -> 
                  Atualizando estoque: 
                  {item['produto']['id']} 
                  {item['produto']['nome']} =
                  {supply} => {estoque}""")

        sqlRES = sql_exe("""UPDATE produtos
                            SET estoque = ?
                            WHERE id = ? """, [estoque, id] )
        
        if sqlRES:
            print("[MS]ESTOQUE -> Database atualizada com sucesso")
        else:
            print("[MS]ESTOQUE -> Falha ao atualizar database")

        return sqlRES

# Auxiliar consume()
def sql_exe(inp, arg=(), head=5):

    print(f"[MS]ESTOQUE -> SQL: {inp} - {str(arg)}")

    with sqlite3.connect("ecommerce.db") as db:

        cursor = db.cursor()
        cursor.execute(inp, arg)

        if inp.strip().lower().startswith("select"):
            return cursor.fetchall()[:head]
        else:
            db.commit()
            return True


if __name__ == "__main__":

    exchanges = {
        'Pedidos_Criados' : 'Pedido.#.Criado',
        'Pedidos_Excluidos' : 'Pedido.#.Excluido',
    }

    pikaConnect(exchanges)
