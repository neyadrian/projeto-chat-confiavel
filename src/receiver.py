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

        if window_start <= packet.seq_num <= window_end:
            print(f"[RAW] Recebido Seq {packet.seq_num} na ordem de chegada. Enviando ACK {packet.seq_num}.")
            send_ack_callback(packet.seq_num)

            if packet.seq_num not in self.buffer:
                self.buffer[packet.seq_num] = packet.payload

            self._slide_window()

        elif (window_start - self.window_size) <= packet.seq_num < window_start:
            print(f"[RAW] Recebido Seq {packet.seq_num} duplicado (antigo). Reenviando ACK {packet.seq_num}.")
            send_ack_callback(packet.seq_num)

        else:
            pass

    def _slide_window(self):
        while self.base_seq in self.buffer:
            payload = self.buffer.pop(self.base_seq)
            
            print(f"[DELIVER] Entregue Seq {self.base_seq} ao usuário: '{payload}'\n")
            
            self.base_seq += 1