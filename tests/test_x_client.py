import unittest

from aleph_nought import AlephXClient, AlephXConfig


class TestXClient(unittest.TestCase):
    def setUp(self):
        self.config = AlephXConfig(
            host="https://aleph.mzk.cz",
            endpoint="X",
            base="MZK01",
        )
        self.client = AlephXClient(self.config)

    def test_is_available(self):
        self.assertTrue(self.client.is_available())

    def test_get_record(self):
        try:
            system_numbers = list(
                self.client.find_system_numbers("BAR", "2610893386")
            )
            self.assertEqual(len(system_numbers), 1)
            self.assertEqual(system_numbers[0], "MZK01-0002610893386")
        except RuntimeError as e:
            if "Error 403 Forbidden" in str(e):
                self.skipTest("X-Server operation not available")
            else:
                raise
