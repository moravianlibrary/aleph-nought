from logging import getLogger
from typing import Generator, Tuple

from lxml import etree
from marcdantic import MarcRecord

from ..config import AlephOAIConfig
from ..record_status import RecordStatus
from ..web_client import AlephWebClient
from .constants import MARC_NS, NS_0, OAI_NS
from .custom_types import OaiVerb

ListRecordResponse = Tuple[str, RecordStatus, MarcRecord | None]


logger = getLogger("aleph_nought")


class AlephOAIClient(AlephWebClient):
    def __init__(self, config: AlephOAIConfig):
        super().__init__(config)
        self._base = config.base

    def is_available(self) -> bool:
        try:
            response = self._session.get(
                f"{self._host}/{self._endpoint}",
                params={"verb": OaiVerb.Identify.value},
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_record(self, base: str, doc_number: str) -> MarcRecord:
        response = self._session.get(
            f"{self._host}/{self._endpoint}",
            params={
                "verb": OaiVerb.GetRecord.value,
                "metadataPrefix": "marc21",
                "identifier": f"oai:aleph.mzk.cz:{base}-{doc_number}",
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

    def list_records(
        self, from_date: str, to_date: str
    ) -> Generator[ListRecordResponse, None, None]:

        params = {
            "verb": OaiVerb.ListRecords.value,
            "metadataPrefix": "marc21",
            "from": from_date,
            "until": to_date,
            "set": self._base,
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

                if header.get("status") == "deleted":
                    yield identifier, RecordStatus.Deleted, None
                    continue

                xml_marc = record_result.find(
                    ".//marc:record", namespaces=MARC_NS
                )
                try:
                    yield MarcRecord.from_xml(xml_marc)
                except Exception as e:
                    logger.error(f"Error processing record {identifier}: {e}")
                    logger.debug(
                        f"Record content: {etree.tostring(record_result)}"
                    )
                    yield identifier, RecordStatus.Failed, None

            resumption_token = content.find(
                ".//oai:resumptionToken", namespaces=OAI_NS
            )
            if resumption_token is None or not resumption_token.text:
                break

            params = {
                "verb": OaiVerb.ListRecords.value,
                "resumptionToken": resumption_token.text,
            }
