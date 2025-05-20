import unittest

from aleph_nought import AlephOAIClient, AlephOAIConfig, RecordStatus


class TestOAIClient(unittest.TestCase):
    def setUp(self):
        self.config = AlephOAIConfig(
            host="https://aleph.mzk.cz",
            endpoint="OAI",
            base="MZK01",
            system_number_pattern="\\d{9}",
            oai_sets=["MZK01-VDK"],
            oai_identifier_template="oai:aleph.mzk.cz:{base}-{doc_number}",
        )
        self.client = AlephOAIClient(self.config)

    def test_is_available(self):
        self.assertTrue(self.client.is_available())

    def test_get_record(self):
        record = self.client.get_record("000960080")
        self.assertIsNotNone(record)
        self.assertEqual(
            record.control_fields.control_number, "nkc20091970515"
        )

    def test_get_record_invalid(self):
        with self.assertRaises(Exception):
            self.client.get_record("MZK01", "invalid_number")

    def test_list_records(self):
        records = list(
            self.client.list_records(
                "2025-03-01T00:00:00Z", "2025-03-02T00:00:00Z"
            )
        )
        self.assertGreater(len(records), 0)
        for record in records:
            self.assertIsNotNone(record)
            if record.base:
                self.assertEqual(record.base, "MZK01")
            self.assertIn(
                record.status, [RecordStatus.Active, RecordStatus.Deleted]
            )
