import re
from logging import getLogger
from typing import Generator, NamedTuple

from lxml import etree
from marcdantic import MarcRecord

from ..config import AlephOAIConfig
from ..record_status import RecordStatus
from ..web_client import AlephWebClient
from .constants import MARC_NS, NS_0, OAI_NS
from .custom_types import OaiVerb


class ListRecordResponse(NamedTuple):
    base: str
    system_number: str
    status: RecordStatus
    record: MarcRecord | None = None


logger = getLogger("aleph_nought")


class AlephOAIClient(AlephWebClient):
    def __init__(self, config: AlephOAIConfig):
        super().__init__(config)
        self._oai_sets = config.oai_sets
        self._oai_identifier_template = config.oai_identifier_template.format(
            base=config.base, doc_number="{doc_number}"
        )
        self._parse_identifier_pattern = self._build_parse_identifier_pattern(
            config.oai_identifier_template,
            config.base,
            config.system_number_pattern,
        )

    def _build_parse_identifier_pattern(
        self,
        template: str,
        base: str,
        system_number_pattern: str,
    ) -> re.Pattern:
        """
        Builds a regex pattern to match OAI identifiers
        from a template and allowed bases.
        """
        pattern = re.escape(template)

        base_pattern = f"(?P<base>{re.escape(base)})"
        system_pattern = f"(?P<system_number>{system_number_pattern})"

        pattern = pattern.replace(re.escape("{base}"), base_pattern)
        pattern = pattern.replace(re.escape("{doc_number}"), system_pattern)

        return re.compile(pattern)

    def is_available(self) -> bool:
        try:
            response = self._session.get(
                f"{self._host}/{self._endpoint}",
                params={"verb": OaiVerb.Identify.value},
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_record(self, doc_number: str) -> MarcRecord:
        response = self._session.get(
            f"{self._host}/{self._endpoint}",
            params={
                "verb": OaiVerb.GetRecord.value,
                "metadataPrefix": "marc21",
                "identifier": self._oai_identifier_template.format(
                    doc_number=doc_number
                ),
            },
        )

        response.raise_for_status()
        content = etree.fromstring(response.content)

        error = content.find(".//ns0:error", namespaces=NS_0)
        if error is not None:
            raise Exception(error.text)

        xml_marc = content.find(".//marc:record", namespaces=MARC_NS)
        if xml_marc is None:
            return None

        return MarcRecord.from_xml(xml_marc)

    def _list_records_in_set(
        self, oai_set: str, from_date: str | None, to_date: str | None
    ) -> Generator[ListRecordResponse, None, None]:

        params = {
            "verb": OaiVerb.ListRecords.value,
            "metadataPrefix": "marc21",
            "from": from_date,
            "until": to_date,
            "set": oai_set,
        }

        while True:
            response = self._session.get(
                f"{self._host}/{self._endpoint}",
                params=params,
            )
            response.raise_for_status()

            content = etree.fromstring(response.content)

            records = content.findall(".//oai:record", namespaces=OAI_NS)
            if not records:
                logger.info("No records found in this batch.")
                break

            for record_result in records:
                header = record_result.find(".//oai:header", namespaces=OAI_NS)

                if header is None:
                    logger.error("Record without header found.")
                    raise Exception("Record without header found.")

                identifier = header.find(
                    ".//oai:identifier", namespaces=OAI_NS
                ).text
                if identifier is None:
                    logger.error("Record without identifier found.")
                    raise Exception("Record without identifier found.")

                match_ = self._parse_identifier_pattern.search(identifier)
                if match_ is None:
                    logger.error(
                        f"Record with invalid identifier found: {identifier}"
                    )
                    raise Exception(
                        f"Record with invalid identifier found: {identifier}"
                    )

                base = match_.group("base")
                system_number = match_.group("system_number")

                if header.get("status") == "deleted":
                    yield ListRecordResponse(
                        base=base,
                        system_number=system_number,
                        status=RecordStatus.Deleted,
                    )
                    continue

                xml_marc = record_result.find(
                    ".//marc:record", namespaces=MARC_NS
                )
                try:
                    yield ListRecordResponse(
                        base=base,
                        system_number=system_number,
                        status=RecordStatus.Active,
                        record=MarcRecord.from_xml(xml_marc),
                    )
                except Exception as e:
                    logger.error(f"Error processing record {identifier}: {e}")
                    logger.debug(
                        f"Record content: {etree.tostring(record_result)}"
                    )
                    yield ListRecordResponse(
                        base=base,
                        system_number=system_number,
                        status=RecordStatus.Failed,
                    )

            resumption_token = content.find(
                ".//oai:resumptionToken", namespaces=OAI_NS
            )
            if resumption_token is None or not resumption_token.text:
                break

            params = {
                "verb": OaiVerb.ListRecords.value,
                "resumptionToken": resumption_token.text,
            }

    def list_records(
        self, from_date: str | None, to_date: str | None
    ) -> Generator[ListRecordResponse, None, None]:
        for oai_set in self._oai_sets:
            yield from self._list_records_in_set(oai_set, from_date, to_date)
