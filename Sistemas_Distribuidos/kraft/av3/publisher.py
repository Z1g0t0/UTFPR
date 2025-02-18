import Pyro5.api
from faker import Faker
import json

if __name__ == "__main__":

    leader = Pyro5.api.Proxy("PYRONAME:Lider_Epoca1")
    fake = Faker()
    timeout = 8
    i = 1

    while True:
        i+=1
        data = {
            fake.name() : {
                'endereco': str(fake.address()),
                'email': str(fake.email()),
                'telefone': str(fake.phone_number())
            }
        }
        print(f"{i}. Dados a serem publicados: ")
        print("=============================================")
        print(json.dumps(data, indent=4))
        print("=============================================")
        
        print("\nPressione enter para publicar")
        input()
        print("Enviando...")
        print(leader.publish(data))
        #try: print(leader.publish(data))
        #except: continue
