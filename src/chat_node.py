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