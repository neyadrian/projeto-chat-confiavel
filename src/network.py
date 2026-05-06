import socket
import random
import logging

from src.config import HOST, BUFFER_SIZE, SIMULATE_LOSS, LOSS_RATE
from src.packet import Packet

logger = logging.getLogger("network")


class UDPSocket:
    def __init__(self, local_port: int, remote_port: int,
                 loss_rate: float = LOSS_RATE, simulate_loss: bool = SIMULATE_LOSS):
        self.local_port = local_port
        self.remote_port = remote_port
        self.loss_rate = loss_rate
        self.simulate_loss = simulate_loss
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, local_port))
        self._remote_addr = (HOST, remote_port)
        logger.info("UDP aberto: %s:%d -> %s:%d", HOST, local_port, HOST, remote_port)

    def send(self, packet: Packet) -> bool:
        raw = packet.to_bytes()
        if self.simulate_loss and random.random() < self.loss_rate:
            logger.warning("[REDE] %s DESCARTADO (perda simulada)", packet)
            return False
        self.sock.sendto(raw, self._remote_addr)
        logger.debug("[REDE] %s enviado", packet)
        return True

    def receive(self, timeout: float = None) -> Packet | None:
        self.sock.settimeout(timeout)
        try:
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            pkt = Packet.from_bytes(data)
            if pkt is None:
                logger.warning("[REDE] Pacote corrompido de %s", addr)
            return pkt
        except (socket.timeout, OSError):
            return None

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def set_loss_rate(self, rate: float):
        self.loss_rate = rate
        logger.info("[REDE] Perda ajustada para %.0f%%", rate * 100)

    def set_simulate_loss(self, enabled: bool):
        self.simulate_loss = enabled
