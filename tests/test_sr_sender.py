import unittest
import threading
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.sr_sender import SRSender
from src.config import WINDOW_SIZE


class MockSocket:
    def __init__(self):
        self.sent_packets = []
        self.lock = threading.Lock()

    def send(self, packet):
        with self.lock:
            self.sent_packets.append(packet)
        return True

    def get_sent(self):
        with self.lock:
            return list(self.sent_packets)

    def clear(self):
        with self.lock:
            self.sent_packets.clear()


class TestSRSenderWindow(unittest.TestCase):
    def setUp(self):
        self.mock = MockSocket()
        self.sender = SRSender(self.mock, window_size=4)
        self.sender.cwnd = float(WINDOW_SIZE)

    def tearDown(self):
        self.sender.stop()

    def test_send_within_window(self):
        for i in range(4):
            self.sender.send(f"msg{i}")
        self.assertEqual(len(self.mock.get_sent()), 4)

    def test_blocks_when_full(self):
        for i in range(4):
            self.sender.send(f"msg{i}")
        blocked = threading.Event()
        t = threading.Thread(target=lambda: (self.sender.send("msg4"), blocked.set()), daemon=True)
        t.start()
        self.assertFalse(blocked.wait(timeout=1.0))
        self.sender.receive_ack(0)
        self.assertTrue(blocked.wait(timeout=2.0))

    def test_window_advance(self):
        for i in range(4):
            self.sender.send(f"msg{i}")
        self.sender.receive_ack(0)
        self.assertEqual(self.sender.base, 1)
        self.sender.receive_ack(1)
        self.assertEqual(self.sender.base, 2)

    def test_cumulative_advance(self):
        for i in range(4):
            self.sender.send(f"msg{i}")
        self.sender.receive_ack(1)
        self.sender.receive_ack(2)
        self.assertEqual(self.sender.base, 0)
        self.sender.receive_ack(0)
        self.assertEqual(self.sender.base, 3)


class TestSRSenderACK(unittest.TestCase):
    def setUp(self):
        self.mock = MockSocket()
        self.sender = SRSender(self.mock, window_size=4)
        self.sender.cwnd = float(WINDOW_SIZE)

    def tearDown(self):
        self.sender.stop()

    def test_dup_ack_counting(self):
        self.sender.send("msg0")
        self.sender.receive_ack(0)
        self.sender.receive_ack(0)
        self.assertEqual(self.sender.dup_ack_count.get(0, 0), 1)
        self.sender.receive_ack(0)
        self.assertEqual(self.sender.dup_ack_count.get(0, 0), 2)

    def test_ack_removes_unacked(self):
        self.sender.send("msg0")
        self.assertIn(0, self.sender.unacked)
        self.sender.receive_ack(0)
        self.assertNotIn(0, self.sender.unacked)


class TestSRSenderTimer(unittest.TestCase):
    def setUp(self):
        self.mock = MockSocket()
        self.sender = SRSender(self.mock, window_size=4)
        self.sender.cwnd = float(WINDOW_SIZE)

    def tearDown(self):
        self.sender.stop()

    def test_timeout_retransmit(self):
        import src.config as config
        orig = config.TIMEOUT
        config.TIMEOUT = 0.5
        self.sender.send("msg0")
        n = len(self.mock.get_sent())
        time.sleep(1.0)
        self.assertGreater(len(self.mock.get_sent()), n)
        config.TIMEOUT = orig

    def test_ack_cancels_timer(self):
        self.sender.send("msg0")
        self.assertIn(0, self.sender.timers)
        self.sender.receive_ack(0)
        self.assertNotIn(0, self.sender.timers)


class TestSRSenderCongestion(unittest.TestCase):
    def setUp(self):
        self.mock = MockSocket()
        self.sender = SRSender(self.mock, window_size=4)

    def tearDown(self):
        self.sender.stop()

    def test_initial_cwnd(self):
        self.assertEqual(self.sender.cwnd, 1.0)

    def test_cwnd_grows(self):
        init = self.sender.cwnd
        self.sender.send("msg0")
        self.sender.receive_ack(0)
        self.assertGreater(self.sender.cwnd, init)

    def test_cwnd_drops_on_loss(self):
        self.sender.cwnd = 4.0
        self.sender._on_loss_detected()
        self.assertEqual(self.sender.cwnd, 1.0)
        self.assertEqual(self.sender.ssthresh, 2.0)

    def test_cwnd_capped(self):
        self.sender.cwnd = float(WINDOW_SIZE)
        self.sender.ssthresh = 1.0
        self.sender.send("msg0")
        self.sender.receive_ack(0)
        self.assertLessEqual(self.sender.cwnd, float(WINDOW_SIZE))


class TestSRSenderStats(unittest.TestCase):
    def setUp(self):
        self.mock = MockSocket()
        self.sender = SRSender(self.mock, window_size=4)
        self.sender.cwnd = float(WINDOW_SIZE)

    def tearDown(self):
        self.sender.stop()

    def test_count_sent(self):
        self.sender.send("a")
        self.sender.send("b")
        self.assertEqual(self.sender.get_stats()["total_sent"], 2)

    def test_initial_zero(self):
        s = self.sender.get_stats()
        self.assertEqual(s["total_sent"], 0)
        self.assertEqual(s["retransmissions"], 0)


if __name__ == "__main__":
    unittest.main()
