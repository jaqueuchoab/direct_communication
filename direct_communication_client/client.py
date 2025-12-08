import socket
import json
import time
import random

HOST = "localhost"
PORT = 5000

# Consultar lista de veículos no servidor
client = socket.socket()
client.connect((HOST, PORT))
client.send("GET_VEICULOS".encode())

data = client.recv(4096).decode()
client.close()

veiculos = json.loads(data)

print("Veículos carregados do servidor:")
for v in veiculos:
    print(" -", v["idVeiculo"])


def gerar_status(veic):
    return {
        "idVeiculo": veic["idVeiculo"],
        "localizacao": {
            "lat": veic["baseLat"] + random.uniform(-0.002, 0.002),
            "long": veic["baseLong"] + random.uniform(-0.002, 0.002)
        },
        "combustivel": random.randint(5, 100),
        "velocidade": random.randint(0, 90),
        "status": random.choice(["operando", "parado", "manutencao"]),
        "hora": time.strftime("%Y-%m-%d %H:%M:%S")
    }


while True:
    for veic in veiculos:
        status = gerar_status(veic)

        print(f"\n🚀 Enviando status de {veic['idVeiculo']}...")
        print(status)

        try:
            client = socket.socket()
            client.connect((HOST, PORT))

            client.send(json.dumps(status).encode())
            resposta = client.recv(1024).decode()

            print("📥 Resposta do servidor:", resposta)

            client.close()
        except Exception as e:
            print("Erro ao enviar:", e)

    time.sleep(5)
