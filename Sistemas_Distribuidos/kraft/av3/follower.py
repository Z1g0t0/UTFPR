import Pyro5.api
from time import sleep, time
from threading import Thread, Lock
import random
import json
import sys

class Follower( object ):

    def __init__(self, epoch, leader, name): 

        self.epoch = epoch
        self.leader = leader
        self.name = name

        self.new = {}
        self.log = {}
      
        # Verifica pelo lider se ha vaga votante,
        #caso nao fica como observador
        self.voter = self.set_status()

        Thread(target=self.receive_msg).start()
        Thread(target=self.send_heartbeat).start()

    def set_status(self):
        proxy = Pyro5.api.Proxy(self.leader)

        return proxy.check_quorum()

    def fetch_new(self):
        
        proxy = Pyro5.api.Proxy(self.leader)
        if not self.log:
            epoch = 1
        else:
            last_entry = self.log[next(reversed(self.log.keys()))]
            epoch = last_entry['Epoch']

        newest = proxy.get_new(epoch, len(self.log))
        
        # Casos excepicionais(ignorar)
        if 'Fatal' in newest:
            print("FATAL ERROR")
            print(f"EPOCH: {self.epoch} | OFFSET: {len(self.log)}")
            return

        elif 'Error' in newest:
            print(f"Atualizando log...")
            print(f"Offset registrado: {len(self.log)} | Atual: {newest['Log_size']}")
            print("Dados atualizados: ")
            print(f"\t{len(newest['Data'])} entrada(s).")

            newest = newest['Data']

        # Log repetido
        elif newest and newest == self.new:
            #print(f"\n{self.name} - Log ja adicionado: ")
            #print(json.dumps(newest, indent=4))
            #print(f"\t***Ignorando atualizacao\n")
            return

        self.new.update(newest)
        self.log.update(self.new.copy())
        
        if self.voter:
            proxy.confirm(name)

        return True
    
    # Usado pelo lider para notificar
    @Pyro5.api.expose
    def receive_msg(self, message={}):
        try:
            print(f"Notificacao: {message['Description']}")
            if message['Type'] == 'WRITE':
                # Simulacao de falha
                r = random.randint(1, 12)
                if r > 3:
                    print("Buscando dados novos...")
                    if self.fetch_new():
                        print(f"\n{self.name} - Dados comitados: ")
                        #print(json.dumps(self.log, indent=4))
                        print(f"{len(self.log)} entrada(s).")

                else:
                    print(f"\n\t***{self.name}: Falha simulada\n")

            elif message['Type'] == 'PROMOTE' and not self.voter:
                print(f"{self.name} -> PROMOVIDO")
                self.voter = True

                Thread(target=self.send_heartbeat).start()

            elif message['Type'] == 'DEMOTE':
                print(f"{self.name} -> DEMOVIDO")
                self.voter = False 

        except KeyError:
            print(f"Tipo de mensagem inesperada: {message}")
            pass

    def send_heartbeat(self):
        proxy = Pyro5.api.Proxy(self.leader)
        self.fetch_new()
        while self.voter:
            r = random.randint(8, 12)
            #r = random.randint(4, 8)
            print(f"{self.name} - Tempo para heartbeat: {r}")
            sleep(r)
            try:
                self.voter = proxy.receive_heartbeat(name)
            except (Pyro5.errors.ConnectionClosedError, 
                    Pyro5.errors.CommunicationError) as e:
                print(f"{self.leader} desconectado.")
                break
        print(f"{self.name} - Seguindo como observador")
        return


if __name__ == "__main__":

    epoch = 1
    leader = "PYRONAME:Lider_Epoca1"
    name = sys.argv[1]
    log = {}

    daemon = Pyro5.server.Daemon()
    follower = Follower(epoch, leader, name)
    uri = daemon.register(follower)

    proxy = Pyro5.api.Proxy(leader) 
    if not proxy.add_uri(name, str(uri)):
        print(f"Nome: {name} ja existe, escolher outro nome")
        sys.exit()

    daemon.requestLoop()

