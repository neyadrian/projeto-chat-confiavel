import json
import zlib


class Packet:
    def __init__(self, pkt_type: str, seq: int, data: str = "", checksum: str = ""):
        self.pkt_type = pkt_type
        self.seq = seq
        self.data = data
        self.checksum = checksum

    def to_bytes(self) -> bytes:
        raw = f"{self.pkt_type}:{self.seq}:{self.data}"
        self.checksum = format(zlib.crc32(raw.encode("utf-8")) & 0xFFFFFFFF, "08x")
        return json.dumps({
            "type": self.pkt_type, "seq": self.seq,
            "data": self.data, "checksum": self.checksum,
        }).encode("utf-8")

    @staticmethod
    def from_bytes(raw_bytes: bytes):
        try:
            d = json.loads(raw_bytes.decode("utf-8"))
            pkt = Packet(d["type"], d["seq"], d.get("data", ""), d.get("checksum", ""))
            raw = f"{pkt.pkt_type}:{pkt.seq}:{pkt.data}"
            expected = format(zlib.crc32(raw.encode("utf-8")) & 0xFFFFFFFF, "08x")
            return pkt if pkt.checksum == expected else None
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
            return None

    @staticmethod
    def make_data(seq: int, data: str) -> "Packet":
        return Packet("DATA", seq, data)

    @staticmethod
    def make_ack(seq: int) -> "Packet":
        return Packet("ACK", seq)

    @property
    def is_ack(self) -> bool:
        return self.pkt_type == "ACK"

    @property
    def is_data(self) -> bool:
        return self.pkt_type == "DATA"

    def __repr__(self):
        if self.is_ack:
            return f"[ACK seq={self.seq}]"
        return f"[DATA seq={self.seq} | '{self.data[:30]}']"