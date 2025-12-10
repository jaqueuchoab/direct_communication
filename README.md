# Comunicação Direta (Socket TCP)
## Sistema de Controle de Frotas

Este projeto implementa o **Cenário A -- Comunicação Direta** da prática
de Sistemas Distribuídos, utilizando **Sockets TCP** para comunicação
entre um **servidor central** e **múltiplos veículos simulados**
(clientes).

Cada veículo envia periodicamente seu **status completo** para o
servidor, que processa regras de negócio, valida atrasos, detecta
veículos offline e exibe tudo em um **Painel Web** para monitoramento.

------------------------------------------------------------------------

## Arquitetura do Sistema

    [Veículos (Clientes)]  →  [Servidor Socket]  →  [Painel Web (Flask)]
              Status TCP                Processamento           Visualização

-   A comunicação é **direta**, feita com **requisições explícitas via
    socket TCP**.
-   O servidor recebe e valida cada mensagem.
-   O painel exibe a situação atual da frota em tempo real.

------------------------------------------------------------------------

## Funcionalidades Implementadas

### 1. Comunicação Direta via Sockets

-   O cliente (veículo) abre conexão TCP com o servidor.
-   Envia seu status em formato JSON.
-   Servidor processa e responde uma mensagem de confirmação.

### 2. Envio Periódico de Status

Cada veículo envia a cada **5 segundos**: - Localização (lat/long) -
Combustível (%) - Velocidade - Estado (operando, parado, manutenção) -
Horário da coleta

### 3. Regras de Negócio

#### ✔ Identificação do veículo

Apenas IDs cadastrados no arquivo `veiculos.json` são aceitos.

#### ✔ Verificação de atraso

Se o veículo ficar **mais de 6s sem enviar**, a resposta indica atraso.

#### ✔ Regras de combustível

-   `< 10%` → **Crítico**
-   `< 20%` → **Baixo**

#### ✔ Detecção automática de OFFLINE

Se um veículo ficar **\> 20s** sem enviar status, é marcado como:

    OFFLINE

------------------------------------------------------------------------

## 🌐 4. Painel Web (Flask)

O servidor também hospeda um painel web acessível em:

**http://localhost:8000**

Ou em outra máquina da rede:

**http://IP_DO_SERVIDOR:8000**

O painel exibe: - ID do veículo\
- Status (ONLINE / OFFLINE / SEM DADOS)\
- Última atualização\
- Combustível\
- Velocidade\
- Alertas de combustível

A página atualiza automaticamente a cada 3 segundos.

------------------------------------------------------------------------

## Estrutura de Arquivos

    /projeto-frota-socket
    │
    ├── servidor.py        # Servidor socket + painel web + regras de negócio
    ├── cliente.py         # Simulador de veículo
    ├── veiculos.json      # Lista de veículos cadastrados
    └── README.md          # Este arquivo

------------------------------------------------------------------------

## Como Executar

### 1. Instalar dependências

    pip install flask

### 2. Executar o servidor

    python servidor.py

Isso inicia: - Servidor socket\
- Painel web em http://localhost:8000\
- Monitor de veículos offline

### 3. Executar um ou mais clientes

    python cliente.py

Também pode rodar em outras máquinas da LAN (alterando o IP do
servidor).

------------------------------------------------------------------------

## Protocolo de Comunicação

O cliente envia:

``` json
{
  "idVeiculo": "CAR-01",
  "localizacao": { "lat": -3.73, "long": -38.51 },
  "combustivel": 42,
  "velocidade": 60,
  "hora": "2025-12-06 14:35:20"
}
```

O servidor responde:

    STATUS RECEBIDO COM SUCESSO

Ou alertas como:

    STATUS RECEBIDO COM ATRASO

------------------------------------------------------------------------

## Testes com Múltiplos Clientes

-   Vários clientes simultâneos\
-   Clientes remotos\
-   Simulação de falha (desligar cliente)\
-   Painel atualiza tudo em tempo real

------------------------------------------------------------------------

## Conclusão

A implementação demonstra: - Comunicação **direta** cliente-servidor\
- Regras reais de monitoramento de frota\
- Detecção de falhas\
- Painel web em tempo real

Um modelo fiel aos sistemas reais utilizados por empresas de transporte
e logística.
