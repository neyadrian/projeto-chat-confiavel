# Chat SR — Selective Repeat sobre UDP

Chat bidirecional confiável implementado em Python usando o protocolo **Selective Repeat** sobre **UDP**.

## Estrutura

```
├── main.py              # Ponto de entrada
├── src/
│   ├── config.py        # Constantes do protocolo
│   ├── packet.py        # Serialização de pacotes (JSON + CRC32)
│   ├── network.py       # Socket UDP + simulação de perdas
│   ├── sr_sender.py     # Emissor SR (janela, timers, fast retransmit, cwnd)
│   ├── sr_receiver.py   # Receptor SR (buffer de reordenação, ACK individual)
│   └── chat.py          # Aplicação de chat (integra sender + receiver)
├── tests/
│   ├── test_packet.py
│   └── test_sr_sender.py
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10+
- Apenas bibliotecas da stdlib (socket, threading, json, zlib, logging)

## Como Usar

**Terminal 1 (Alice):**
```bash
python main.py A
```

**Terminal 2 (Bob):**
```bash
python main.py B
```

### Opções

| Flag | Descrição |
|------|-----------|
| `--loss RATE` | Taxa de perda simulada (padrão: 0.2) |
| `--no-loss` | Desativa simulação de perda |
| `--debug` | Ativa logging DEBUG |

### Comandos no Chat

| Comando | Ação |
|---------|------|
| `/sair` | Encerra o chat |
| `/stats` | Mostra estatísticas (enviados, retransmissões, cwnd, etc.) |
| `/raw` | Mostra log de chegada na ordem real |
| `/loss X` | Ajusta taxa de perda em tempo real |
| `/help` | Ajuda |

## Testes

```bash
python -m pytest tests/ -v
```

ou

```bash
python -m unittest discover tests/
```

## Funcionalidades

- **Janela deslizante N=4** (emissor e receptor)
- **ACK individual** por pacote (não cumulativo)
- **Buffer de reordenação** com `dict {seq: dados}`
- **Timer por pacote** via `threading.Timer`
- **Bloqueio** quando buffer cheio (não descarta)
- **Fast Retransmit** (3 ACKs duplicados)
- **Congestion Avoidance** (slow start + additive increase)
- **Checksum CRC32** para integridade
- **Simulação de perdas** configurável
- **Duas saídas**: ordem de chegada (RAW) e ordem de entrega (ENTREGUE)
