import threading
from packet import Packet

class Sender:
    def __init__(self, send_packet_callback, max_window: int = 4, timeout: float = 3.0):
        self.send_packet_callback = send_packet_callback
        self.max_window = max_window
        self.timeout = timeout
        
        self.base_seq = 0
        self.next_seq = 0
        self.window_size = 1 
        
        self.message_queue = []       
        self.packets = {}             
        self.timers = {}              
        self.acked = set()            
        
        self.last_ack_received = -1
        self.dup_ack_count = 0
        
        self.lock = threading.Lock()

    def send_mesage(self, payload: str):
        with self.lock:
            self.message_queue.append(payload)
            self._try_send()

    def _try_send(self):
        while self.message_queue and (self.next_seq < self.base_seq + int(self.window_size)):
            payload = self.message_queue.pop(0)
            packet = Packet(seq_num=self.next_seq, is_ack=False, payload=payload)
            
            self.packets[self.next_seq] = packet
            self._send_and_start_timer(packet)
            
            self.next_seq += 1

    def _send_and_start_timer(self, packet: Packet, is_retransmit: bool = False):
        tag = "[RETRANSMIT]" if is_retransmit else "[SEND]"
        print(f"{tag} Seq {packet.seq_num} | Janela atual: {int(self.window_size)}")
        
        self.send_packet_callback(packet.to_bytes())
        
        if packet.seq_num in self.timers:
            self.timers[packet.seq_num].cancel()
            
        timer = threading.Timer(self.timeout, self._handle_timeout, args=(packet.seq_num,))
        self.timers[packet.seq_num] = timer
        timer.start()