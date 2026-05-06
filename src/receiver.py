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

        
