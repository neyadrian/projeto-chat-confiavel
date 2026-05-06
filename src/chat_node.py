import socket
import threading
from packet import Packet
from sender import Sender
from receiver import Receiver

class ChatNode:
    def __init__(self, my_ip: str, my_port: int, peer_ip: str, peer_port: int):
        self.my_address = (my_ip, my_port)
        self.peer_address = (peer_ip, peer_port)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.my_address)
        
        self.sender = Sender(send_packet_callback=self._send_raw_bytes)
        self.receiver = Receiver(window_size=4)
        
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen, daemon=True)
        self.listen_thread.start()

    def _send_raw_bytes(self, data: bytes):
        self.sock.sendto(data, self.peer_address)

    def _send_ack(self, seq_num: int):
        ack_packet = Packet(seq_num=seq_num, is_ack=True)
        self._send_raw_bytes(ack_packet.to_bytes())

    def _listen(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
                packet = Packet.from_bytes(data)
                
                if packet is None:
                    continue  
                    
                if packet.is_ack:
                    self.sender.process_ack(packet.seq_num)
                else:
                    self.receiver.receive_packet(packet, send_ack_callback=self._send_ack)
                    
            except OSError:
                if self.running:
                    print("Socket fechado de forma inesperada.")
                break

    def send_chat_message(self, text: str):
        self.sender.send_message(text)
        
    def stop(self):
        self.running = False
        self.sock.close()