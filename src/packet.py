import json

class Packet:
    def __init__(self, seq_num: int, is_ack: bool = False, payload: str = ""):
        self.seq_num = seq_num
        self.is_ack = is_ack
        self.payload = payload

    def to_bytes(self) -> bytes:
        packet_dict = {
            "seq_num": self.seq_num,
            "is_ack": self.is_ack,
            "payload": self.payload
        }
        return json.dumps(packet_dict).encode('utf-8')
    
    @staticmethod
    def from_bytes(data: bytes):
        try:
            packet_dict = json.loads(data.decode('utf-8'))
            return Packet(
                seq_num = packet_dict["seq_num"],
                is_ack = packet_dict["is_ack"],
                payload = packet_dict.get("payload", "")
            )
        except json.JSONDecodeError:
            print("Erro: Pacote corrompido recebido.")
            return None
        except KeyError as e:
            print(f"Erro: Pacote mal formatado, faltando chave {e}")
            return None
        
    def __str__(self):
        tipo = "ACK" if self.is_ack else "DATA"
        return f"[{tipo} | Seq: {self.seq_num} | Payload: '{self.payload}']"