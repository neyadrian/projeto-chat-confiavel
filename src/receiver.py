class Receiver:
    def __init__(self, window_size: int = 4):
        self.window_size = window_size
        self.base_seq = 0
        self.buffer = {}

    def receive_packet(self, packet, send_ack_callback):
        if packet.is_ack:
            return

        window_start = self.base_seq
        window_end = self.base_seq + self.window_size - 1

        if window_start <= packet.seq <= window_end:
            print(f"[RAW] Recebido Seq {packet.seq} na ordem de chegada. Enviando ACK {packet.seq}.")
            send_ack_callback(packet.seq)

            if packet.seq not in self.buffer:
                self.buffer[packet.seq] = packet.data

            self._slide_window()

        elif (window_start - self.window_size) <= packet.seq < window_start:
            print(f"[RAW] Recebido Seq {packet.seq} duplicado (antigo). Reenviando ACK {packet.seq}.")
            send_ack_callback(packet.seq)

        else:
            pass

    def _slide_window(self):
        while self.base_seq in self.buffer:
            data = self.buffer.pop(self.base_seq)

            print(f"[DELIVER] Entregue Seq {self.base_seq} ao usuário: '{data}'\n")

            self.base_seq += 1