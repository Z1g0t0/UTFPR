import database
from pydantic import BaseModel

from faker import Faker
import faker_commerce as fc

import random
import sys

class Produto( BaseModel ):
    id : int 
    nome : str
    preco : float
    estoque : int

db = database.SessionLocal()
database.Base.metadata.create_all(bind=database.engine)

if __name__ == "__main__":

    fake = Faker()
    fake.add_provider(fc.Provider)
    #n = input("Quantidade de produtos: ")
    n = sys.argv[1]
    print("Gerando " + n + " produtos")
    
    names = []
    for i in range(int(n)):
        name = fake.ecommerce_name()
        if str(name) in names:
            continue
        names.append(str(name))
        preco = round(random.uniform(11.11, 1111.11), 2)
        p = Produto( id = i, 
                     nome = name,
                     preco = preco,
                     estoque = random.randint(11,111) )

        print(p.model_dump())
        
        produto = database.Produto(**p.model_dump())

        db.add(produto)
        db.commit()
        db.refresh(produto)
     

