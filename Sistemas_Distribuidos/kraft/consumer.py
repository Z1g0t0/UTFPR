import Pyro5.api
import json

if __name__ == "__main__":

    leader = Pyro5.api.Proxy("PYRONAME:Lider_Epoca1")

    while True:
        data = leader.get_log()
        print(f"Dados a encontrados: {json.dumps(data, indent=4)}")
        print(f"\nTotal de entrada(s): {len(data)}")
        print("\nPressione qualquer tecla novamente")
        input("=============================================\n")

