import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.packet import Packet


class TestPacketCreation(unittest.TestCase):
    def test_make_data(self):
        pkt = Packet.make_data(seq=0, data="Ola mundo")
        self.assertEqual(pkt.pkt_type, "DATA")
        self.assertEqual(pkt.seq, 0)
        self.assertTrue(pkt.is_data)
        self.assertFalse(pkt.is_ack)

    def test_make_ack(self):
        pkt = Packet.make_ack(seq=5)
        self.assertEqual(pkt.pkt_type, "ACK")
        self.assertEqual(pkt.seq, 5)
        self.assertTrue(pkt.is_ack)

    def test_repr(self):
        self.assertIn("DATA", repr(Packet.make_data(3, "teste")))
        self.assertIn("ACK", repr(Packet.make_ack(7)))


class TestPacketSerialization(unittest.TestCase):
    def test_round_trip_data(self):
        orig = Packet.make_data(seq=2, data="Mensagem de teste")
        restored = Packet.from_bytes(orig.to_bytes())
        self.assertIsNotNone(restored)
        self.assertEqual(restored.pkt_type, "DATA")
        self.assertEqual(restored.seq, 2)
        self.assertEqual(restored.data, "Mensagem de teste")

    def test_round_trip_ack(self):
        restored = Packet.from_bytes(Packet.make_ack(10).to_bytes())
        self.assertIsNotNone(restored)
        self.assertEqual(restored.pkt_type, "ACK")

    def test_round_trip_unicode(self):
        orig = Packet.make_data(0, "Cafe ☕ resume 中文")
        restored = Packet.from_bytes(orig.to_bytes())
        self.assertIsNotNone(restored)
        self.assertEqual(restored.data, "Cafe ☕ resume 中文")

    def test_empty_data(self):
        restored = Packet.from_bytes(Packet.make_data(0, "").to_bytes())
        self.assertIsNotNone(restored)

    def test_large_seq(self):
        restored = Packet.from_bytes(Packet.make_data(255, "x").to_bytes())
        self.assertEqual(restored.seq, 255)


class TestPacketChecksum(unittest.TestCase):
    def test_valid(self):
        self.assertIsNotNone(Packet.from_bytes(Packet.make_data(0, "t").to_bytes()))

    def test_corrupted(self):
        raw = bytearray(Packet.make_data(0, "teste").to_bytes())
        if len(raw) > 10:
            raw[10] = (raw[10] + 1) % 256
        Packet.from_bytes(bytes(raw))

    def test_invalid_json(self):
        self.assertIsNone(Packet.from_bytes(b"nao eh json"))

    def test_incomplete_json(self):
        self.assertIsNone(Packet.from_bytes(b'{"type": "DATA"'))

    def test_missing_fields(self):
        import json
        self.assertIsNone(Packet.from_bytes(json.dumps({"type": "DATA"}).encode()))


if __name__ == "__main__":
    unittest.main()
