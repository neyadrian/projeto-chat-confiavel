import threading
import logging

from src.config import WINDOW_SIZE, MAX_SEQ_NUM
from src.packet import Packet

logger = logging.getLogger("sr_receiver")


class SRReceiver:
    def __init__(self, network_socket, on_deliver, window_size: int = WINDOW_SIZE):
        self.net = network_socket
        self.on_deliver = on_deliver
        self.window_size = window_size

        self.expected_seq = 0
        self.buffer = {}
        self.delivered = set()

        self.lock = threading.Lock()
        self.buffer_space = threading.Event()
        self.buffer_space.set()
        self.running = True

        self.stats = {
            "total_received": 0, "delivered": 0,
            "duplicates": 0, "out_of_order": 0,
        }
        self.raw_arrival_log = []

    def receive(self, packet: Packet):
        seq = packet.seq
        data = packet.data

        with self.lock:
            self.stats["total_received"] += 1
            self.raw_arrival_log.append((seq, data))
            logger.info("[RAW RECV] seq=%d | '%s'", seq, data[:50])

            if seq in self.delivered and not self._in_window(seq):
                self.stats["duplicates"] += 1
                self._send_ack(seq)
                return

            if self._in_window(seq):
                while len(self.buffer) >= self.window_size and seq not in self.buffer:
                    if not self.running:
                        return
                    self.lock.release()
                    self.buffer_space.clear()
                    self.buffer_space.wait(timeout=0.5)
                    self.lock.acquire()

                self._send_ack(seq)

                if seq == self.expected_seq % MAX_SEQ_NUM:
                    self._deliver(seq, data)
                    self.expected_seq += 1
                    self._flush_buffer()
                else:
                    if seq not in self.buffer:
                        self.buffer[seq] = data
                        self.stats["out_of_order"] += 1
                        logger.info("[BUFFER] seq=%d (esperando %d)", seq, self.expected_seq % MAX_SEQ_NUM)
            else:
                self.stats["duplicates"] += 1
                self._send_ack(seq)

    def _in_window(self, seq: int) -> bool:
        base = self.expected_seq % MAX_SEQ_NUM
        for i in range(self.window_size):
            if (base + i) % MAX_SEQ_NUM == seq:
                return True
        return False

    def _deliver(self, seq: int, data: str):
        self.delivered.add(seq)
        self.stats["delivered"] += 1
        logger.info("[ENTREGUE] seq=%d | '%s'", seq, data[:50])
        if self.on_deliver:
            self.on_deliver(seq, data)

    def _flush_buffer(self):
        while True:
            ns = self.expected_seq % MAX_SEQ_NUM
            if ns in self.buffer:
                data = self.buffer.pop(ns)
                self._deliver(ns, data)
                self.expected_seq += 1
                self.buffer_space.set()
            else:
                break

    def _send_ack(self, seq: int):
        ack = Packet.make_ack(seq)
        self.net.send(ack)
        logger.debug("[ACK SENT] seq=%d", seq)

    def stop(self):
        self.running = False
        self.buffer_space.set()

    def get_stats(self) -> dict:
        with self.lock:
            return dict(self.stats)

    def get_raw_log(self) -> list:
        with self.lock:
            return list(self.raw_arrival_log)
