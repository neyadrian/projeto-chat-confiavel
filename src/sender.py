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