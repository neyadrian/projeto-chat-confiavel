# 🌐 Chat Confiável via UDP (Selective Repeat)

Este projeto implementa um sistema de chat bidirecional confiável utilizando o protocolo de transporte **UDP**, construindo sobre ele as garantias do protocolo **Selective Repeat (SR)**.

O objetivo é contornar a natureza não confiável do UDP, implementando controle de fluxo, reordenação de pacotes e recuperação de perdas diretamente na camada de aplicação.

---

## 🎯 Finalidade e Contexto Acadêmico

No protocolo UDP padrão, as mensagens podem ser perdidas, duplicadas ou entregues fora de ordem.

Este projeto resolve isso através do **Selective Repeat**, onde:
- O transmissor retransmite apenas os pacotes perdidos
- O receptor aceita pacotes fora de ordem
- Os dados são armazenados em buffer até que possam ser entregues corretamente

---

## ✨ Requisitos Técnicos Implementados

- **Janela Deslizante:** tamanho máximo de janela `N = 4`
- **ACK Individual:** confirmações não cumulativas
- **Buffer de Recepção Ordenado:** usando `dict` (Hash Map) com acesso `O(1)`
- **Timers Individuais:** via `threading.Timer`
- **Fila de Espera (Buffer de Envio):** evita perda de mensagens do usuário
- **Fast Retransmit (Bônus):** retransmissão após 3 ACKs duplicados
- **Congestion Avoidance (Bônus):**
  - Slow Start iniciando em 1
  - Crescimento até 4
  - Redução de 50% em caso de perda

---

## 📁 Estrutura do Projeto

    projeto_chat/
    ├── main.py
    ├── README.md
    └── src/
        ├── packet.py
        ├── sender.py
        ├── receiver.py
        └── chat_node.py

---

## 🚀 Como Executar

O projeto utiliza apenas a Standard Library do Python:
- socket
- threading
- json

### Requisitos
- Python 3.8 ou superior

---

### ▶️ Passo 1: Iniciar o Primeiro Usuário (Nó A)

    python main.py

Configuração:

    Sua porta: 5000
    Porta destino: 5001

---

### ▶️ Passo 2: Iniciar o Segundo Usuário (Nó B)

    python main.py

Configuração:

    Sua porta: 5001
    Porta destino: 5000

---

## 💡 Dica: Salvando Logs

    python main.py | tee chat_log.txt

---

## 📊 Análise: Ordem de Chegada vs Entrega

### 📥 [RAW] — Ordem de Chegada
- Pacote chegou na rede
- ACK enviado imediatamente
- Pode estar fora de ordem

### 📤 [DELIVER] — Ordem de Entrega
- Pacote entregue ao usuário
- Ordem garantida

---

### 🧪 Exemplo de Execução

Chegada fora de ordem: 3 → 1 → 2

    [RAW] Recebido Seq 3. Enviando ACK 3.
    # Pacote fora de ordem → armazenado no buffer

    [RAW] Recebido Seq 1. Enviando ACK 1.
    [DELIVER] Entregue Seq 1: 'Oi!'
    # Base avança para 2

    [RAW] Recebido Seq 2. Enviando ACK 2.
    [DELIVER] Entregue Seq 2: 'Tudo'
    [DELIVER] Entregue Seq 3: 'Bem?'

---

## 👥 Autores

Projeto desenvolvido para a disciplina de Redes de Computadores  
Curso: Engenharia de Software — IFCE (Campus Acopiara)

- Ney Adrian  
- Ítalo Renan  
- Isaque Almeida  
- Yuri Carlos  
- Joarley Anderson  
- Isaías Veríssimo  