import socket
import json
import time
import random
import threading

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


def rotina_veiculo(veic):
    vid = veic["idVeiculo"]

    while True:

        # 10% de chance de ficar OFFLINE por 20-40s
        if random.random() < 0.10:
            off = random.uniform(20, 40)
            print(f"[{vid}] Simulando OFFLINE por {off:.1f}s...")
            time.sleep(off)
            continue

        # gera dados normais
        status = gerar_status(veic)
        print(f"\nEnviando status de {vid}...")
        print(status)

        # 15% de chance de atraso artificial 5–20s
        if random.random() < 0.15:
            atraso = random.uniform(5, 20)
            print(f"[{vid}] Atraso simulado de {atraso:.1f}s...")
            time.sleep(atraso)

        # envia ao servidor
        try:
            client = socket.socket()
            client.connect((HOST, PORT))
            client.send(json.dumps(status).encode())

            resposta = client.recv(1024).decode()
            print(f"[{vid}] Resposta servidor: {resposta}")

            client.close()
        except Exception as e:
            print(f"[{vid}] ERRO ao enviar:", e)

        # intervalo individual (5 a 12s)
        intervalo = random.uniform(5, 12)
        time.sleep(intervalo)


# cria 1 thread para cada veículo
for veic in veiculos:
    t = threading.Thread(target=rotina_veiculo, args=(veic,))
    t.daemon = True
    t.start()

# mantém o programa vivo
while True:
    time.sleep(1)
