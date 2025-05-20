import unittest

from aleph_nought import AlephZ3950Client, AlephZ3950Config


class TestZ3950Client(unittest.TestCase):
    def setUp(self):
        self.config = AlephZ3950Config(
            host="aleph.mzk.cz", port=9991, base="MZK01-UTF"
        )
        self.client = AlephZ3950Client(self.config)

    def test_get_record(self):
        records = list(self.client.search("@attr 1=12 000862960"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].control_fields.control_number, "000862960")
