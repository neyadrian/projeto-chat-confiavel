import threading
import logging

from src.config import (
    WINDOW_SIZE, MAX_SEQ_NUM, TIMEOUT,
    DUP_ACK_THRESHOLD, INITIAL_CWND, INITIAL_SSTHRESH,
)
from src.packet import Packet

logger = logging.getLogger("sr_sender")


class SRSender:
    def __init__(self, network_socket, window_size: int = WINDOW_SIZE):
        self.net = network_socket
        self.window_size = window_size

        self.base = 0
        self.next_seq = 0
        self.unacked = {}
        self.timers = {}
        self.acked = set()

        self.cwnd = float(INITIAL_CWND)
        self.ssthresh = float(INITIAL_SSTHRESH)
        self.acks_in_cwnd = 0

        self.dup_ack_count = {}

        self.lock = threading.Lock()
        self.window_available = threading.Event()
        self.window_available.set()
        self.running = True

        self.stats = {
            "total_sent": 0, "retransmissions": 0,
            "fast_retransmits": 0, "timeouts": 0,
        }

    @property
    def effective_window(self) -> int:
        return min(int(self.cwnd), self.window_size)

    def _window_has_space(self) -> bool:
        return (self.next_seq - self.base) < self.effective_window

    def send(self, data: str):
        while True:
            with self.lock:
                if self._window_has_space() and self.running:
                    break
            if not self.running:
                return
            self.window_available.clear()
            self.window_available.wait(timeout=0.5)

        with self.lock:
            seq = self.next_seq % MAX_SEQ_NUM
            pkt = Packet.make_data(seq, data)
            self.unacked[seq] = pkt
            self.next_seq += 1
            self.stats["total_sent"] += 1
            self.net.send(pkt)
            logger.info("[SEND] %s", pkt)
            self._start_timer(seq)

    def receive_ack(self, ack_seq: int):
        with self.lock:
            if ack_seq in self.acked:
                self.dup_ack_count[ack_seq] = self.dup_ack_count.get(ack_seq, 0) + 1
                count = self.dup_ack_count[ack_seq]
                logger.debug("[DUP ACK] seq=%d (cnt: %d)", ack_seq, count)
                if count >= DUP_ACK_THRESHOLD:
                    self._fast_retransmit(ack_seq)
                return

            self.acked.add(ack_seq)
            self._cancel_timer(ack_seq)
            self.unacked.pop(ack_seq, None)
            logger.info("[ACK RECV] seq=%d", ack_seq)
            self._advance_window()
            self._on_ack_received()
            self.window_available.set()

    def _advance_window(self):
        while (self.base % MAX_SEQ_NUM) in self.acked:
            old = self.base % MAX_SEQ_NUM
            self.acked.discard(old)
            self.dup_ack_count.pop(old, None)
            self.base += 1
        logger.debug("[WIN] base=%d next=%d ew=%d cwnd=%.1f",
                     self.base % MAX_SEQ_NUM, self.next_seq % MAX_SEQ_NUM,
                     self.effective_window, self.cwnd)

    def _start_timer(self, seq: int):
        self._cancel_timer(seq)
        t = threading.Timer(TIMEOUT, self._on_timeout, args=[seq])
        t.daemon = True
        t.start()
        self.timers[seq] = t

    def _cancel_timer(self, seq: int):
        if seq in self.timers:
            self.timers[seq].cancel()
            del self.timers[seq]

    def _on_timeout(self, seq: int):
        with self.lock:
            if seq not in self.unacked:
                return
            pkt = self.unacked[seq]
            self.stats["retransmissions"] += 1
            self.stats["timeouts"] += 1
            logger.warning("[TIMEOUT] seq=%d retransmitindo", seq)
            self._on_loss_detected()
            self.net.send(pkt)
            self._start_timer(seq)

    def _fast_retransmit(self, ack_seq: int):
        target = self.base % MAX_SEQ_NUM
        if target in self.unacked:
            pkt = self.unacked[target]
            self.stats["retransmissions"] += 1
            self.stats["fast_retransmits"] += 1
            logger.warning("[FAST RT] seq=%d (3 dup acks seq=%d)", target, ack_seq)
            self._on_loss_detected()
            self._cancel_timer(target)
            self.net.send(pkt)
            self._start_timer(target)
            self.dup_ack_count[ack_seq] = 0

    def _on_ack_received(self):
        if self.cwnd < self.ssthresh:
            self.cwnd += 1.0
        else:
            self.cwnd += 1.0 / self.cwnd
        self.cwnd = min(self.cwnd, float(self.window_size))

    def _on_loss_detected(self):
        self.ssthresh = max(self.cwnd / 2.0, 1.0)
        self.cwnd = 1.0
        logger.info("[CWND] perda: cwnd=%.1f ssthresh=%.1f", self.cwnd, self.ssthresh)

    def stop(self):
        self.running = False
        self.window_available.set()
        with self.lock:
            for seq in list(self.timers):
                self._cancel_timer(seq)

    def get_stats(self) -> dict:
        with self.lock:
            return dict(self.stats)
