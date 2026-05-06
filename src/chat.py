import threading
import logging
import sys

from src.config import (
    HOST, WINDOW_SIZE,
    LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT,
    SIMULATE_LOSS, LOSS_RATE,
)
from src.network import UDPSocket
from src.sr_sender import SRSender
from src.sr_receiver import SRReceiver
from src.packet import Packet

logger = logging.getLogger("chat")


class Chat:
    def __init__(self, name: str, local_port: int, remote_port: int,
                 loss_rate: float = LOSS_RATE, simulate_loss: bool = SIMULATE_LOSS,
                 log_level: str = LOG_LEVEL):
        self.name = name
        self.running = False
        self._setup_logging(log_level)
        self.net = UDPSocket(local_port, remote_port, loss_rate, simulate_loss)
        self.sender = SRSender(self.net)
        self.receiver = SRReceiver(self.net, on_deliver=self._on_message_delivered)
        self.messages_delivered = []
        self.lock = threading.Lock()

    def _setup_logging(self, level: str):
        numeric = getattr(logging, level.upper(), logging.INFO)
        root = logging.getLogger()
        root.setLevel(numeric)
        root.handlers.clear()

        fh = logging.FileHandler(f"chat_{self.name.lower()}.log", mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root.addHandler(fh)

        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root.addHandler(ch)

    def _on_message_delivered(self, seq: int, data: str):
        with self.lock:
            self.messages_delivered.append((seq, data))
        print(f"\r  [ENTREGUE] seq={seq} | {data}")
        print(f"  [{self.name}] Voce: ", end="", flush=True)

    def _receive_loop(self):
        while self.running:
            pkt = self.net.receive(timeout=0.5)
            if pkt is None:
                continue
            if pkt.is_ack:
                self.sender.receive_ack(pkt.seq)
            elif pkt.is_data:
                print(f"\r  [RAW recv] seq={pkt.seq} | {pkt.data}")
                print(f"  [{self.name}] Voce: ", end="", flush=True)
                self.receiver.receive(pkt)

    def _send_loop(self):
        while self.running:
            try:
                msg = input(f"  [{self.name}] Voce: ")
                if not msg:
                    continue
                if msg.lower() == "/sair":
                    self.stop()
                    break
                elif msg.lower() == "/stats":
                    self._show_stats()
                    continue
                elif msg.lower() == "/raw":
                    self._show_raw_log()
                    continue
                elif msg.lower().startswith("/loss "):
                    try:
                        rate = float(msg.split()[1])
                        self.net.set_loss_rate(rate)
                        print(f"  [SISTEMA] Perda ajustada para {rate*100:.0f}%")
                    except (ValueError, IndexError):
                        print("  [SISTEMA] Uso: /loss 0.3")
                    continue
                elif msg.lower() == "/help":
                    self._show_help()
                    continue
                self.sender.send(f"{self.name}: {msg}")
            except (EOFError, KeyboardInterrupt):
                self.stop()
                break

    def _show_banner(self):
        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║       CHAT SR — Selective Repeat / UDP       ║")
        print("  ╠══════════════════════════════════════════════╣")
        print(f"  ║  Terminal: {self.name:<35}║")
        print(f"  ║  Porta local:  {self.net.local_port:<31}║")
        print(f"  ║  Porta remota: {self.net.remote_port:<31}║")
        print(f"  ║  Janela (N):   {WINDOW_SIZE:<31}║")
        print(f"  ║  Perda sim.:   {'Sim' if self.net.simulate_loss else 'Nao':<31}║")
        if self.net.simulate_loss:
            print(f"  ║  Taxa perda:   {self.net.loss_rate*100:.0f}%{'':<29}║")
        print("  ╠══════════════════════════════════════════════╣")
        print("  ║  /sair /stats /raw /loss X /help             ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()

    def _show_stats(self):
        ss = self.sender.get_stats()
        rs = self.receiver.get_stats()
        print()
        print("  ┌─── Emissor ────────────────────────────────┐")
        print(f"  │  Enviados:     {ss['total_sent']:<28}│")
        print(f"  │  Retransmit:   {ss['retransmissions']:<28}│")
        print(f"  │  Fast RT:      {ss['fast_retransmits']:<28}│")
        print(f"  │  Timeouts:     {ss['timeouts']:<28}│")
        print(f"  │  cwnd:         {self.sender.cwnd:<28.1f}│")
        print(f"  │  ssthresh:     {self.sender.ssthresh:<28.1f}│")
        print("  └────────────────────────────────────────────┘")
        print("  ┌─── Receptor ───────────────────────────────┐")
        print(f"  │  Recebidos:    {rs['total_received']:<28}│")
        print(f"  │  Entregues:    {rs['delivered']:<28}│")
        print(f"  │  Duplicatas:   {rs['duplicates']:<28}│")
        print(f"  │  Fora ordem:   {rs['out_of_order']:<28}│")
        print("  └────────────────────────────────────────────┘")
        print()

    def _show_raw_log(self):
        raw = self.receiver.get_raw_log()
        print()
        print("  ┌─── Log de Chegada (ordem real) ────────────┐")
        if not raw:
            print("  │  (nenhum pacote recebido)                   │")
        for i, (seq, data) in enumerate(raw[-10:]):
            print(f"  │  #{i+1:>3} | seq={seq:<3} | {data[:30]:<30} │")
        if len(raw) > 10:
            print(f"  │  ... e mais {len(raw)-10} anteriores               │")
        print("  └────────────────────────────────────────────┘")
        print()

    def _show_help(self):
        print()
        print("  /sair   — encerrar    /stats — estatisticas")
        print("  /raw    — log chegada /loss X — ajustar perda")
        print()

    def start(self):
        self.running = True
        self._show_banner()
        recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        recv_thread.start()
        try:
            self._send_loop()
        except Exception as e:
            logger.error("Erro: %s", e)
        finally:
            self.stop()

    def stop(self):
        if not self.running:
            return
        self.running = False
        print("\n  [SISTEMA] Encerrando...")
        self.sender.stop()
        self.receiver.stop()
        self._show_stats()
        self.net.close()
