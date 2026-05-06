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

    def send_message(self, payload: str):
        with self.lock:
            self.message_queue.append(payload)
            self._try_send()

    def _try_send(self):
        while self.message_queue and (self.next_seq < self.base_seq + int(self.window_size)):
            payload = self.message_queue.pop(0)
            packet = Packet.make_data(self.next_seq, payload)

            self.packets[self.next_seq] = packet
            self._send_and_start_timer(packet)

            self.next_seq += 1

    def _send_and_start_timer(self, packet: Packet, is_retransmit: bool = False):
        tag = "[RETRANSMIT]" if is_retransmit else "[SEND]"
        print(f"{tag} Seq {packet.seq} | Janela atual: {int(self.window_size)}")

        self.send_packet_callback(packet.to_bytes())

        if packet.seq in self.timers:
            self.timers[packet.seq].cancel()

        timer = threading.Timer(self.timeout, self._handle_timeout, args=(packet.seq,))
        self.timers[packet.seq] = timer
        timer.start()

    def _handle_timeout(self, seq_num: int):
        with self.lock:
            if seq_num in self.acked:
                return  
            
            print(f"[TIMEOUT] Pacote Seq {seq_num} perdido!")
            self._apply_congestion_penalty()
            
            packet = self.packets[seq_num]
            self._send_and_start_timer(packet, is_retransmit=True)

    def process_ack(self, ack_seq: int):
        with self.lock:
            if ack_seq == self.last_ack_received:
                self.dup_ack_count += 1
                if self.dup_ack_count == 3:
                    print(f"[FAST RETRANSMIT] 3 ACKs duplicados para Seq {ack_seq}. Retransmitindo base ({self.base_seq})!")
                    self._apply_congestion_penalty()
                    if self.base_seq in self.packets and self.base_seq not in self.acked:
                        self._send_and_start_timer(self.packets[self.base_seq], is_retransmit=True)
                    self.dup_ack_count = 0 
            else:
                self.last_ack_received = ack_seq
                self.dup_ack_count = 1

            if ack_seq in self.acked or ack_seq < self.base_seq:
                return

            print(f"[ACK] Recebido ACK {ack_seq}.")
            self.acked.add(ack_seq)
            
            if ack_seq in self.timers:
                self.timers[ack_seq].cancel()
                del self.timers[ack_seq]

            if self.window_size < self.max_window:
                self.window_size += 1

            if ack_seq == self.base_seq:
                self._slide_window()

    def _slide_window(self):
        while self.base_seq in self.acked:
            self.acked.remove(self.base_seq)
            if self.base_seq in self.packets:
                del self.packets[self.base_seq]
                
            self.base_seq += 1
            
        self._try_send()

    def _apply_congestion_penalty(self):
        self.window_size = max(1, self.window_size // 2)
        print(f"[CONGESTION] Janela reduzida para {self.window_size}")