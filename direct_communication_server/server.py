import socket
import json
import time
import threading
from flask import Flask, jsonify, render_template_string

HOST = "localhost"
PORT = 5000

# Carrega os veículos cadastrados no arq .json
with open("veiculos.json", "r") as f:
    veiculos_cadastrados = json.load(f)

ids_validos = {v["idVeiculo"] for v in veiculos_cadastrados}
print("Veículos cadastrados:", ids_validos)

# Guarda último timestamp e estado atual e guarda o último status completo
last_update = {}
status_atual = {}
ultimo_status = {}  

# THREAD PARA VERIFICAR VEÍCULO OFFLINE
def verificar_offline():
    while True:
        agora = time.time()
        for vid in ids_validos:
            if vid in last_update:
                diff = agora - last_update[vid]
                if diff > 20:
                    status_atual[vid] = "OFFLINE"
            else:
                status_atual[vid] = "SEM DADOS"
        time.sleep(5)

thread_checker = threading.Thread(target=verificar_offline)
thread_checker.daemon = True
thread_checker.start()

# SERVIDOR SOCKET
def socket_server():
    server = socket.socket()
    server.bind((HOST, PORT))
    server.listen()

    print(f"Servidor Socket iniciado em {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        data = conn.recv(4096).decode()

        # Cliente pedindo lista de veículos
        if data == "GET_VEICULOS":
            conn.send(json.dumps(veiculos_cadastrados).encode())
            conn.close()
            continue

        # Cliente enviou status
        status = json.loads(data)
        id_veic = status["idVeiculo"]

        if id_veic not in ids_validos:
            conn.send("VEICULO_DESCONHECIDO".encode())
            conn.close()
            continue

        timestamp_recebido = time.time()

        print(f"\n📩 Status recebido de {id_veic}:")
        print(status)

        # registra último status
        ultimo_status[id_veic] = status

        # Verifica atraso
        if id_veic in last_update:
            diff = timestamp_recebido - last_update[id_veic]
            if diff > 6:
                resposta = "STATUS RECEBIDO COM ATRASO"
            else:
                resposta = "STATUS RECEBIDO COM SUCESSO"
        else:
            resposta = "PRIMEIRO STATUS RECEBIDO"

        last_update[id_veic] = timestamp_recebido
        status_atual[id_veic] = "ONLINE"

        # Regra de combustível
        combustivel = status["combustivel"]

        if combustivel < 10:
            resposta += " | COMBUSTÍVEL CRÍTICO"
        elif combustivel < 20:
            resposta += " | COMBUSTÍVEL BAIXO"

        conn.send(resposta.encode())
        conn.close()


thread_socket = threading.Thread(target=socket_server)
thread_socket.daemon = True
thread_socket.start()

# SERVIDOR WEB (Flask)
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Painel da Frota</title>
<style>
body { font-family: Arial; background: #f5f5f5; padding: 20px; }
.card { background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 0 5px #ccc; }
.online { color: green; font-weight: bold; }
.offline { color: red; font-weight: bold; }
.semdados { color: gray; font-weight: bold; }
</style>
<script>
async function atualizar() {
    const res = await fetch('/status');
    const dados = await res.json();

    let div = document.getElementById("conteudo");
    div.innerHTML = "";

    dados.forEach(v => {
        div.innerHTML += `
        <div class='card'>
            <h2>${v.id}</h2>
            <p>Status: <span class="${v.estado.toLowerCase()}">${v.estado}</span></p>
            <p>Última atualização: ${v.ultima_atualizacao}</p>
            <p>Combustível: ${v.combustivel}%</p>
            <p>Velocidade: ${v.velocidade} km/h</p>
            <p>Alerta: ${v.alerta}</p>
        </div>`;
    });
}

setInterval(atualizar, 3000);
window.onload = atualizar;
</script>
</head>
<body>
<h1>Painel de Monitoramento da Frota</h1>
<div id="conteudo"></div>
</body>
</html>
"""

@app.route("/")
def painel():
    return render_template_string(HTML)

@app.route("/status")
def get_status():
    resposta = []

    for v in veiculos_cadastrados:
        vid = v["idVeiculo"]
        dado = ultimo_status.get(vid, None)

        if vid in status_atual:
            estado = status_atual[vid]
        else:
            estado = "SEM DADOS"

        if dado:
            combustivel = dado["combustivel"]
            velocidade = dado["velocidade"]
            alerta = ""

            if combustivel < 10:
                alerta = "CRÍTICO"
            elif combustivel < 20:
                alerta = "Baixo"
            else:
                alerta = "OK"

            ultima = time.strftime("%H:%M:%S", time.localtime(last_update[vid]))
        else:
            combustivel = "-"
            velocidade = "-"
            alerta = "-"
            ultima = "-"

        resposta.append({
            "id": vid,
            "estado": estado,
            "ultima_atualizacao": ultima,
            "combustivel": combustivel,
            "velocidade": velocidade,
            "alerta": alerta
        })

    return jsonify(resposta)


# Inicia o servidor web Flask
app.run(host="0.0.0.0", port=8000, debug=False)

