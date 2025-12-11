import socket
import json
import time
import random
import threading

HOST = "localhost"
PORT = 5000

# etapa 1: estabelecer comunicação com o servidor por meio do socket e consultar quais são os veículos disponíveis
# a var client cria um socket, isso permitirá a comunicação com o servidor podendo receber, enviar dados e fechar a conexão
client = socket.socket()
client.connect((HOST, PORT))
# a função send envia uma mensagem em forma de bytes para o servidor, que nesse caso, é uma solicitação da lista de veículos
client.send("GET_VEICULOS".encode())

# a var data guarda a resposta do servidor sockets, que também vem em forma de bytes e deve ser decodificada para string (o num indica o max de bytes)
data = client.recv(4096).decode()
# a conexão é fechada, importante para liberação de veículos
client.close()

veiculos = json.loads(data)

print("Veículos carregados do servidor:")
for v in veiculos:
    print(" -", v["idVeiculo"])

# função que gera status aleatórios para cada veículo informado pelo servidor
def gerar_status(veic):
    return {
        "idVeiculo": veic["idVeiculo"],
        "localizacao": {
            "lat": veic["baseLat"] + random.uniform(-0.002, 0.002),
            "long": veic["baseLong"] + random.uniform(-0.002, 0.002)
        },
        "combustivel": random.randint(5, 100),
        "velocidade": random.randint(0, 90),
        "hora": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# função que define uma rotina para cada veiculo
def rotina_veiculo(veic):
    vid = veic["idVeiculo"]

    while True:

        # 10% de chance de ficar OFFLINE por 20-40s | perda de sinal, queda de conexão
        if random.random() < 0.10:
            off = random.uniform(20, 40)
            print(f"[{vid}] Simulando OFFLINE por {off:.1f}s...")
            # indica que o veiculo deve ficar x segundos sem enviar nada
            time.sleep(off)
            continue

        # gera dados normais, sem intercorrências
        status = gerar_status(veic)
        print(f"\nEnviando status de {vid}...")
        print(status)

        # 15% de chance de atraso artificial 5–20s | congestionamento de rede, lentidão no envio de dados
        if random.random() < 0.15:
            atraso = random.uniform(5, 20)
            print(f"[{vid}] Atraso simulado de {atraso:.1f}s...")
            time.sleep(atraso)

        # envio para o servidor
        try:
            client = socket.socket()
            client.connect((HOST, PORT))
            # envio do status convertido em json no formato de bytes
            client.send(json.dumps(status).encode())

            # aguarda resposta do servidor
            resposta = client.recv(1024).decode()
            print(f"[{vid}] Resposta servidor: {resposta}")

            client.close()
        except Exception as e:
            print(f"[{vid}] ERRO ao enviar:", e)

        # intervalo individual (5 a 12s), evita a sincronização entre os veiculos
        intervalo = random.uniform(5, 12)
        time.sleep(intervalo)

# cria uma thread para cada veículo, a fim de simular uma rotina realista, logo, cada veículo tem sua própria "rotina"
# isso demonstra a independência de cada veículo
for veic in veiculos:
    # criação da thread para o veículo da vez, que executa a função rotina_veiculo
    t = threading.Thread(target=rotina_veiculo, args=(veic,))
    # define como execução em segundo plano, e encerrada sozinha quando o o programa principal termina
    t.daemon = True
    t.start()

# mantém o programa vivo
while True:
    time.sleep(1)
