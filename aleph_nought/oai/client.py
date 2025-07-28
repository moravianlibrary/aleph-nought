import re
from logging import getLogger
from typing import Generator, NamedTuple

from lxml import etree
from marcdantic import MarcRecord

from ..config import AlephOAIConfig
from ..record_status import RecordStatus
from ..web_client import AlephWebClient
from .definitions import MARC_NS, NS_0, OAI_NS, OaiVerb


class ListRecordResponse(NamedTuple):
    base: str
    system_number: str
    status: RecordStatus
    record: MarcRecord | None = None


logger = getLogger("aleph_nought")


class AlephOAIClient(AlephWebClient):
    """
    Client for accessing OAI-PMH services from an Aleph system.

    This client provides methods to check service availability, fetch
    individual MARC records, and harvest records from configured OAI sets.

    For more information on the OAI-PMH protocol, see:
    https://www.openarchives.org/OAI/openarchivesprotocol.html#ProtocolSyntax

    Arguments
    ---------
    config : AlephOAIConfig
        Configuration for the OAI client, including base URL, endpoint,
        OAI sets, and identifier template.

    Methods
    -------
    is_available() -> bool:
        Checks if the OAI service is available by sending an Identify request.
    get_record(doc_number: str) -> MarcRecord | None:
        Fetches a record by its document number using the GetRecord verb.
    list_records(
        from_date: str | None, to_date: str | None
    ) -> Generator[ListRecordResponse, None, None]:
        Harvest records from all configured OAI sets,
        optionally filtered by date.
    """

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
        Build a regex pattern to parse OAI identifiers based on a template.

        This method generates a compiled regular expression pattern from
        a given identifier template. The template must include placeholders
        `{base}` and `{doc_number}`, which are replaced with the appropriate
        regex sub-patterns.

        Parameters
        ----------
        template : str
            A string template representing the structure of the identifier,
            containing `{base}` and `{doc_number}` placeholders.
        base : str
            The expected literal string for the base component
            of the identifier.
        system_number_pattern : str
            A regex pattern that matches the document number in the identifier.

        Returns
        -------
        re.Pattern
            A compiled regular expression pattern with named groups `base` and
            `system_number`, suitable for parsing identifiers.

        Examples
        --------
        >>> pattern = obj._build_parse_identifier_pattern(
        ...     template='oai:aleph.mzk.cz:{base}-{doc_number}',
        ...     base='MZK01',
        ...     system_number_pattern='\\d{9}'
        ... )
        >>> match = pattern.match('oai:aleph.mzk.cz:MZK01-123456789')
        >>> match.groupdict()
        {'base': 'MZK01', 'system_number': '123456789'}
        """
        pattern = re.escape(template)

        base_pattern = f"(?P<base>{re.escape(base)})"
        system_pattern = f"(?P<system_number>{system_number_pattern})"

        pattern = pattern.replace(re.escape("{base}"), base_pattern)
        pattern = pattern.replace(re.escape("{doc_number}"), system_pattern)

        return re.compile(pattern)

    def is_available(self) -> bool:
        """
        Check if the OAI-PMH endpoint is available.

        This method sends a request to the configured OAI-PMH endpoint using
        the `Identify` verb to determine if the service is reachable and
        responding correctly.

        Returns
        -------
        bool
            `True` if the endpoint responds with HTTP status code 200,
            indicating availability; `False` otherwise.

        Notes
        -----
        Any exceptions raised during the request
        (e.g., connection errors, timeouts) are caught,
        and `False` is returned in such cases.
        """
        try:
            response = self._session.get(
                f"{self._host}/{self._endpoint}",
                params={"verb": OaiVerb.Identify.value},
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_record(self, doc_number: str) -> MarcRecord | None:
        """
        Retrieve a MARC record from the OAI-PMH endpoint by document number.

        This method sends a `GetRecord` request to the OAI-PMH endpoint using
        the provided document number. It expects the record to be in
        MARC21 format and parses the XML response into a `MarcRecord` object.

        Parameters
        ----------
        doc_number : str
            The document identifier to use in the OAI-PMH request.

        Returns
        -------
        MarcRecord or None
            A `MarcRecord` object parsed from the response if found,
            or `None` if no MARC record is present in the response.

        Raises
        ------
        Exception
            If the OAI-PMH response contains an error message or if the HTTP
            request fails (non-2xx status codes).

        Notes
        -----
        - The `identifier` parameter is constructed using the instance's
          configured `self._oai_identifier_template`.
        - The method uses the `marc21` metadata format.
        """
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
        """
        List MARC records in a given OAI set within an optional date range.

        This method sends paginated `ListRecords` requests to
        an OAI-PMH endpoint for a specified set.
        It yields `ListRecordResponse` objects for each record,
        which may represent active, deleted, or failed records.

        Parameters
        ----------
        oai_set : str
            The identifier of the OAI set to harvest records from.
        from_date : str or None
            The start date (inclusive) of the harvesting window
            in `YYYY-MM-DD` format. If `None`, no lower date bound is used.
        to_date : str or None
            The end date (inclusive) of the harvesting window
            in `YYYY-MM-DD` format. If `None`, no upper date bound is used.

        Yields
        ------
        ListRecordResponse
            A response object for each harvested record, including status and
            optionally the parsed `MarcRecord`.

        Raises
        ------
        Exception
            If a record is missing required elements
            (e.g., header or identifier), or if identifier parsing fails.

        Notes
        -----
        - Records are fetched in batches using resumption tokens for
          pagination.
        - Deleted records are yielded with status `RecordStatus.Deleted`.
        - If parsing of a MARC record fails, the record is yielded with status
          `RecordStatus.Failed`.
        """

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
        """
        Harvest all MARC records across configured OAI sets within
        an optional date range.

        This is a wrapper around `_list_records_in_set` that iterates over all
        configured OAI sets and yields their records.

        Parameters
        ----------
        from_date : str or None
            The start date (inclusive) of the harvesting window
            in `YYYY-MM-DD` format. If `None`, no lower date bound is applied.
        to_date : str or None
            The end date (inclusive) of the harvesting window
            in `YYYY-MM-DD` format. If `None`, no upper date bound is applied.

        Yields
        ------
        ListRecordResponse
            A response object for each harvested record from all OAI sets.

        Notes
        -----
        - This method delegates the record harvesting to
          `_list_records_in_set` for each set listed in `self._oai_sets`.
        """

        for oai_set in self._oai_sets:
            yield from self._list_records_in_set(oai_set, from_date, to_date)
