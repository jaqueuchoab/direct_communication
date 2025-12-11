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

# função que verifica se o veiculo está online ou offline, roda a cada 5s e se o veiculo passou mais de 20s sem status é marcado como off
def verificar_offline():
    while True:
        now = time.time()
        for vid in ids_validos:
            if vid in last_update:
                diff = now - last_update[vid]
                if diff > 20:
                    status_atual[vid] = "OFFLINE"
            else:
                status_atual[vid] = "SEM DADOS"
        time.sleep(5)

# thread que roda a função de verificação de status a cada 5s 
thread_checker = threading.Thread(target=verificar_offline)
thread_checker.daemon = True
thread_checker.start()

# definição do servidor - imprime os logs no terminal
def socket_server():
    server = socket.socket()
    # estabelece por onde será feita a comunicação, podendo receber e enviar dados
    server.bind((HOST, PORT))
    # dá inicio à escuta de seus clientes
    server.listen()

    print(f"Servidor Socket iniciado em {HOST}:{PORT}")

    while True:
        # defije a aceitação de mensagens de seus clientes (veiculos)
        conn, addr = server.accept()
        # recebe o json enviado por cada cliente
        data = conn.recv(4096).decode()

        # solicitação da lista de veículos
        if data == "GET_VEICULOS":
            conn.send(json.dumps(veiculos_cadastrados).encode())
            conn.close()
            continue

        # recebimento de envio de status do cliente, como a unica coisa que será recebida são os status não é necessário definir uma mensagem
        status = json.loads(data)
        id_veic = status["idVeiculo"]

        if id_veic not in ids_validos:
            conn.send("VEICULO_DESCONHECIDO".encode())
            conn.close()
            continue

        # horário de recebimento dos dados
        timestamp_recebido = time.time()

        print(f"\nStatus recebido de {id_veic}:")
        print(status)

        # registra último status
        ultimo_status[id_veic] = status

        # verifica atraso se já há algum status disponível, se não, indica o recebimento de primeiro status
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

        # regra de combustível
        combustivel = status["combustivel"]

        if combustivel < 10:
            resposta += "COMBUSTÍVEL CRÍTICO"
        elif combustivel < 20:
            resposta += "COMBUSTÍVEL BAIXO"

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

    <link rel="icon" type="image/png" href="./static/favcon.ico">

    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');
        
        h1 {
            color: #FFF;
            font-weight: 600;
        }
        
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;

            font-family: Inter; 
            background: #2d2276;
        }

        .content {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            grid-template-rows: 1fr;
            grid-gap: 1rem;

            width: 85%;
            margin-bottom: 20px;
        }
        
        .card { 
            color: #120850;
            background: #f1f0ff; 
            padding: 15px;
            border-radius: 10px; 
            box-shadow: 0 0 5px #ccc; 
        }

        .card > h2 {
            text-align: center;
            margin: 0 0 15px 0;
        }

        .card-dados {
            background: #c8bfff;
            padding: 5px 20px;
            border-radius: 10px;
        }

        .card-dados > p {
            margin: 5px 0;
        }

        .card-dados > p > span {
            font-weight: bold;
        }
        
        .online { 
            color: green;
        }
        
        .offline { 
            color: red; 
        }

        .critico {
            color: red;
        }

        .baixo {
            color: #d43d05;
        }

        .normal {
            color: green;
        }

        #toggle {
            margin: 10px 0 20px 0; 
            padding: 10px 20px; 
            border: none; 
            background: #f1f0ff; 
            color: #120850; 
            font-weight: 600; 
            font-size: 16px;
            border-radius: 10px; 
            cursor: pointer;
        }

        #map {
            height: 400px;
            margin: 0 0 40px 0;
            border-radius: 10px;
            box-shadow: 0 0 5px #ccc;
            width: 85%;
        }

        .veic-map {
            background: #f4642f;
            width: 100%;
            color: #120850;
            border-radius: 10px; 

            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            padding-bottom: 40px;
        }
    </style>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script>
        let mapa;
        let marcadores = {};

        function iniciarMapa() {
            mapa = L.map("map").setView([-3.7288, -40.9923], 15);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19
            }).addTo(mapa);
        }

        let mostrarTodos = false;

        async function atualizar() {
            const res = await fetch('/status');
            const dados = await res.json();

            let div = document.querySelector(".content");
            div.innerHTML = "";

            let listaExibida = mostrarTodos ? dados : dados.slice(0, 5);

            listaExibida.forEach(v => {
                div.innerHTML += `
                <div class='card'>
                    <h2>${v.id}</h2>
                    <div class='card-dados'>
                        <p>Status:</br> <span class="${v.estado.toLowerCase()}">${v.estado}</span></p>
                        <p>Última atualização:</br> <span>${v.ultima_atualizacao}</span></p>
                        <p>Combustível:</br> <span>${v.combustivel}%</span></p>
                        <p>Velocidade:</br> <span>${v.velocidade} km/h</br> - ${v.situation}</span></p>
                        <p>Alerta:</br> <span class="${v.alerta.toLowerCase().replace('í', 'i')}">${v.alerta}</span></p>
                    </div>
                </div>`;
            });

            dados.forEach(v => {
                if (v.lat && v.long) {
                    let cor;

                    if (v.estado === "ONLINE") cor = "green";
                    else if (v.estado === "OFFLINE") cor = "red";
                    else cor = "gray";

                    let icone = L.icon({
                        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${cor}.png`,
                        iconSize: [25, 41],
                        iconAnchor: [12, 41]
                    });

                    if (marcadores[v.id]) {
                        marcadores[v.id].setLatLng([v.lat, v.long]);
                        marcadores[v.id].setIcon(icone);
                    } else {
                        marcadores[v.id] = L.marker([v.lat, v.long], { icon: icone })
                            .addTo(mapa)
                            .bindPopup(`<b>${v.id}</b><br>`);
                    }
                }
            });

            document.getElementById("toggle").textContent = 
            mostrarTodos ? "Mostrar Menos" : "Mostrar Mais";
        }

        setInterval(atualizar, 3000);
        window.onload = () => {
            iniciarMapa();
            atualizar();
        };

        document.addEventListener("DOMContentLoaded", () => {
            document.getElementById("toggle").onclick = () => {
                mostrarTodos = !mostrarTodos;
                atualizar();
            };
        });
    </script>
</head>
<body>
    <h1>Monitoramento de Frota</h1>
    <div class="content"></div>
    <button id="toggle">Mostrar Mais</button>
    <div class="veic-map">
        <h1>Acompanhamento de Veículos</h1>
        <div id="map"></div>
    </div>
</body>
</html>
"""

@app.route("/")
def painel():
    return render_template_string(HTML)

# rota que serve os status de forma analisada
@app.route("/status")
# função que processa e transforma os dados internos em JSON para o navegador 
def get_status():
    resposta = []

    for v in veiculos_cadastrados:
        vid = v["idVeiculo"]
        dado = ultimo_status.get(vid, None)

        # para cada veiculo dentro de status atual, se não houver nenhum, define estado do veiculo como sem dados
        if vid in status_atual:
            estado = status_atual[vid]
        else:
            estado = "SEM DADOS"

        # verifica se há status existente na variável dado, 
        # se sim processa as informações dele e se não retorna um JSON indicando a indisponibilidade dos dados
        if dado:
            combustivel = dado["combustivel"]
            velocidade = dado["velocidade"]

            # processamento dos dados de combustível, verificações necessárias
            if combustivel < 10:
                alerta = "CRÍTICO"
            elif combustivel < 20:
                alerta = "BAIXO"
            else:
                alerta = "NORMAL"

            # processamento dos dados de velocidade, verificações necessárias
            if (velocidade == 0): 
                situation = "PARADO"
            elif (velocidade > 0 and velocidade <= 60):
                situation = "OPERANDO"
            elif (velocidade > 60):
                situation = "EM ALERTA"

            ultima_atual = time.strftime("%H:%M:%S", time.localtime(last_update[vid]))

            lat = dado["localizacao"]["lat"]
            long = dado["localizacao"]["long"]
        else:
            combustivel = "Dados indisponíveis"
            velocidade = "Dados indisponíveis"
            alerta = "Dados indisponíveis"
            ultima_atual = "Dados indisponíveis"
            situation = "Dados indisponíveis"
            lat = None
            long = None

        resposta.append({
            "id": vid,
            "estado": estado,
            "ultima_atualizacao": ultima_atual,
            "combustivel": combustivel,
            "velocidade": velocidade,
            "alerta": alerta,
            "situation": situation,
            "lat": lat,
            "long": long
        })

    return jsonify(resposta)

# inicia o servidor web Flask
app.run(host="0.0.0.0", port=8000, debug=False)