"""A client's configured MarcContext reaches the records it parses.

Every client hands `config.context` to `MarcRecord.from_xml`/`from_mrc`, but
until marcdantic 0.3.13 the mandatory-field part of that context was read from
a private attribute assigned only after validation had already run. A
deployment configuring `mandatory_fields` got the default regardless, and
nothing said so.

0.3.14 put the indicator pattern in the same context, for the same reason:
a record whose indicator the standard does not define used to be refused by
the parser, so neither the record nor the error in it reached anybody.
"""

import unittest

from lxml import etree
from marcdantic import MarcRecord
from marcdantic.context import MarcContext
from marcdantic.fields import DEFAULT_INDICATOR_PATTERN

from aleph_nought import AlephOAIConfig

MARC_NS = "http://www.loc.gov/MARC21/slim"


def _record_xml(*control, ind1="1"):
    fields = "".join(f'<controlfield tag="{t}">000000</controlfield>' for t in control)
    return etree.fromstring(
        f'<record xmlns="{MARC_NS}">'
        "<leader>00000nam a2200000 a 4500</leader>"
        f"{fields}"
        f'<datafield tag="245" ind1="{ind1}" ind2="0">'
        '<subfield code="a">Title</subfield>'
        "</datafield>"
        "</record>".encode()
    )


def _config(context=None):
    return AlephOAIConfig(
        host="https://aleph.mzk.cz",
        endpoint="OAI",
        base="MZK01",
        system_number_pattern="\\d{9}",
        oai_sets=["MZK01-VDK"],
        oai_identifier_template="oai:aleph.mzk.cz:{base}-{doc_number}",
        **({"context": context} if context else {}),
    )


class TestTheConfiguredContextIsHonoured(unittest.TestCase):
    def test_the_default_config_still_requires_005_and_008(self):
        config = _config()

        with self.assertRaises(ValueError) as caught:
            MarcRecord.from_xml(_record_xml("001"), config.context)

        self.assertIn("005", str(caught.exception))
        self.assertIn("008", str(caught.exception))

    def test_a_config_asking_for_less_now_gets_it(self):
        config = _config(MarcContext(mandatory_fields=["001"]))

        record = MarcRecord.from_xml(_record_xml("001"), config.context)

        self.assertEqual(record.fixed_fields.root["001"], "000000")

    def test_the_default_context_is_unchanged(self):
        # The bump must not quietly relax what a deployment already relies on.
        self.assertEqual(
            _config().context.mandatory_fields, ["001", "005", "008"]
        )


class TestTheConfiguredIndicatorPatternIsHonoured(unittest.TestCase):
    """What an indicator may hold is the deployment's call, not the parser's.

    MZK03-001252166 carries ind1="S" on a 500. Harvesting it used to raise,
    so the record never arrived and nobody was told its indicator was wrong.
    """

    def _parse(self, ind1, context=None):
        config = _config(context)
        record = MarcRecord.from_xml(
            _record_xml("001", "005", "008", ind1=ind1), config.context
        )
        return record.variable_fields.root["245"][0]

    def test_the_default_config_takes_an_indicator_outside_the_standard(self):
        self.assertEqual(self._parse("S").ind1, "S")

    def test_a_config_may_hold_records_to_marc_21(self):
        with self.assertRaises(ValueError) as caught:
            self._parse("S", MarcContext(indicator_pattern=r"^[0-9a-z| ]?$"))

        self.assertIn("'S'", str(caught.exception))

    def test_a_tighter_pattern_still_takes_what_it_allows(self):
        field = self._parse("1", MarcContext(indicator_pattern=r"^[0-9a-z| ]?$"))

        self.assertEqual(field.ind1, "1")

    def test_the_default_context_is_unchanged(self):
        # The bump must not quietly tighten what a deployment already parses.
        self.assertEqual(
            _config().context.indicator_pattern, DEFAULT_INDICATOR_PATTERN
        )


if __name__ == "__main__":
    unittest.main()
