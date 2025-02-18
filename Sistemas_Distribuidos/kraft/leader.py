import Pyro5.api
from time import sleep, perf_counter as pc
from threading import Thread
import json

class Lider( object ):

    def __init__( self, epoch, quorum_size, timeout):

        self.epoch = epoch
        self.current_size = 0 
        self.quorum_size = quorum_size

        self.heartbeats = {}
        self.timeout = timeout

        self.uris = {}

        # Dicionario usado para os votantes
        #confirmarem recebimento de log
        self.confirmed = {}

        # Uncommited e log comprometido
        self.new = {}
        self.log = {}

        self.messages = { 
            '1' : { 'Type' : 'WRITE',
                    'Description' : 
                        'Novos dados escritos por publicador' },
            '2' : { 'Type' : 'PROMOTE',
                    'Description' : 
                        'Nova promocao disponivel' },
            '3' : { 'Type' : 'DEMOTE',
                    'Description' : 
                        'Demovido para observador' } }

        Thread(target=self.receive_heartbeat).start()
        Thread(target=self.check_heartbeats).start()

        print("Lider inicializado")

    @Pyro5.api.expose
    def get_log(self):
        return self.log.copy()

    @Pyro5.api.expose
    def confirm(self, name):
        self.confirmed[name] = True

    @Pyro5.api.expose
    def add_uri(self, name, uri):
        #print(f"SELF.URIS: {self.uris}")
        if name not in self.uris:
            self.uris[name] = uri
            print(f"URI adicionado: {uri}")
            return True
        else:
            print(f"Membro: {name} ja existe")
            return False


    # Verifica se ha vaga no quorum
    @Pyro5.api.expose
    def check_quorum(self):
        #print(f"QUORUM: {self.quorum_size} | CURRENT: {self.current_size}")
        return self.quorum_size > self.current_size

    def members(self, silent=False):

        voters = set(self.heartbeats.keys())
        observers = voters ^ set(self.uris.keys())

        if not silent:
            print("\n=============================================")
            print(f"QUORUM: {voters}")
            print(f"OBSERVADORES: {observers}")
            print("=============================================\n")

        # Retorna lista de seguidores
        return voters, observers

    @Pyro5.api.expose
    def get_new(self, epoch, offset):
        
        log_size = len(self.log)

        # Verifica offset e epoca do seguidor
        if offset == log_size and epoch == self.epoch:
            return self.new.copy()
        elif offset < log_size:
            #print("Erro: inconsistencia de offset")
            if offset == 0:
                data = self.new
            else:
                entries = list(self.new.items())
                data = dict(entries[offset:])
            msg = { 'Error' : 'Inconsistencia de offset',
                    'Epoch' : self.epoch,                 
                    'Log_size' : len(self.new),             
                    'Data' : data }          
            return msg
                   
        else: 
            print(f"EPOCH : {epoch} | OFFSET = {offset}")
            print(f"SELF.EPOCH: {self.epoch} | LOG_SIZE= {log_size}")
            return {'Fatal' : 'erro'}

    def notify(self, followers, number):

        print(f"Notificando: {followers}")

        for name in followers:
            try: 
                proxy = Pyro5.api.Proxy(str(self.uris[name])) 
                proxy.receive_msg(self.messages[number])
            except (Pyro5.errors.CommunicationError,
                    ConnectionRefusedError, KeyError):
                print(f"Notificacao para {name} sem resposta.")
                print("Retirando da lista de uris\n")
                try: self.uris.pop(name)
                except KeyError: pass
                
                self.remove([name])

    @Pyro5.api.expose
    def receive_heartbeat(self, name=None):
        if name == None:
            return

        voters, observers = self.members()
        print(f"Líder: Heartbeat recebido de {name}")

        now = round(pc()%1000, 3)

        # Se nao estiver como votante 
        if name not in voters:
            if not self.check_quorum():
                print(f"Quorum ja esta preenchido: {self.quorum_size}")
                return False
            else: 
                #print(f"{self.quorum_size} | {self.current_size}")
                print(f"Lider: Novo votante adicionado: {name}")
                self.heartbeats[name] = now
                self.current_size = len(self.heartbeats)
                self.notify([name], '2')
                self.members()
                return True
        
        self.heartbeats[name] = now
        return True

    def check_heartbeats(self):

        while True:
            
            # Casos excepicionais(ignorar)
            if self.current_size > self.quorum_size:
                print("!!! Quorum supercedido")
                last = list(self.heartbeats.keys())[-1]
                self.remove([last], True)

            # Tempo de agora para comparar contra timeout
            now = round(pc()%1000, 3)

            failed = []

            # Nome, tempo do hearbeat registrado
            for voter, hb in self.heartbeats.items():
                duration = now-hb

                if duration > self.timeout:
                    print(f"""\n!!! Timeout do seguidor: {voter} !!! \n Tempo: {now} | Ultimo HB: {hb} | >{self.timeout}s""")
                    failed.append(voter)
           
            # Demove os votantes que falharam e notifica-os
            if failed: self.remove(failed, True)

            sleep(self.timeout)

    def remove(self, failed, noti=False):
        self.members()
        for voter in failed:
            try: 
                self.heartbeats.pop(voter)
                self.current_size=len(self.heartbeats)
            except KeyError: pass
        
        if noti: self.notify([voter], '3')
        self.members()

        # Caso haja vaga no quorum promover observadores
        if self.check_quorum: 
            observers = self.members(silent=True)[1]
            self.notify(observers, '2')
            
    # Usado pelo publicador(publisher.py)
    @Pyro5.api.expose
    def publish(self, data):
        sleep(self.timeout/2)
        print(f">>> Lider - dados recebidos: ")
        print(json.dumps(data, indent=4) )

        now = pc()
        self.new[str(now)] = { 
            'Epoch' : self.epoch,
            'Offset' : len(self.log),
            'Data' : data.copy()
        }
        
        # Reseta dicionario de confirmacao
        voters, observers = self.members(silent=True)
        self.confirmed.clear()
        for voter in voters: self.confirmed[voter] = False 

        print("Comitando...\n")

        self.notify(voters, '1')
       
        while not all(value for value in self.confirmed.values()):

            print(f"!Erro!: falta confirmacao de log dos votantes.")
            print(f"Confirmados: {self.confirmed}")
            for k, v in self.confirmed.items():
                if not v:
                    print(f"Reenviando dados para {k}.\n")
                    self.notify([k], '1')
            
        print(f"Confirmacoes: {self.confirmed}")
        self.notify(observers, '1')
        self.log.update(self.new.copy()) 

        return f"Lider - dados: \n{json.dumps(data, indent=4)} - Comitados com sucesso."
        

if __name__ == "__main__":

    epoch = 1
    quorum_size = 2
    timeout = 12
    #timeout = 9

    daemon = Pyro5.server.Daemon()         
    leader = Lider(epoch, quorum_size, timeout)
    uri = daemon.register(leader)

    ns = Pyro5.api.locate_ns()
    ns.register("Lider_Epoca1", uri)   
    
    daemon.requestLoop()
