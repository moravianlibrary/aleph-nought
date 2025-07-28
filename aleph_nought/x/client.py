from typing import Generator, Tuple

from lxml import etree

from ..config import AlephXConfig
from ..web_client import AlephWebClient
from .definitions import XOperation


class AlephXClient(AlephWebClient):
    """
    Client for interacting with the Ex Libris Aleph X-Server API.

    The Aleph X-Server API allows external systems to communicate with
    the Aleph integrated library system using HTTP-based queries. This client
    provides a high-level interface for accessing X-Server endpoints,
    including support for searching system numbers by field,
    retrieving paginated search results, and performing single-result lookups.

    It wraps common operations like `find-doc`, `find`, and `present` behind
    methods using structured configuration and response parsing via lxml.

    For full API documentation, refer to:
    https://developers.exlibrisgroup.com/aleph/apis/aleph-x-services/

    Parameters
    ----------
    config : AlephXConfig
        Configuration object for the X-Server client, including host,
        endpoint, base code, and page size.

    Methods
    -------
    is_available() -> bool
        Check if the Aleph X-Server is reachable by sending a ping request.
    find_system_numbers(field: str, value: str) -> Generator[str, None, None]
        Search for system numbers using the specified field and value.
        Returns a generator over all matching document numbers.
    get_one_or_none_system_number(field: str, value: str) -> str | None
        Search for a single system number;
        returns None if not exactly one match.

    Notes
    -----
    - Individual X operations can be blacklisted or whitelisted in the
      X-Server configuration. Therefore, some operations used by this client
      might not be available depending on the server setup
      and user permissions.
    """

    def __init__(self, config: AlephXConfig):
        super().__init__(config)
        self._base = config.base
        self._page_size = config.page_size

    def is_available(self) -> bool:
        """
        Check if the Aleph X-Server is reachable.

        Sends a simple `ping` request to verify that the X-Server endpoint
        is online and responsive.

        Returns
        -------
        bool
            `True` if the server responds with HTTP 200 status;
            `False` otherwise.

        Notes
        -----
        Any exceptions (e.g., timeout, connection failure) are caught,
        and `False` is returned instead of raising.
        """
        try:
            response = self._session.get(
                f"{self._host}/{self._endpoint}",
                params={"op": XOperation.Ping.value},
            )
            return response.status_code == 200
        except Exception:
            return False

    def _search(self, field: str, value: str) -> Tuple[str, int]:
        """
        Perform a fielded search using Aleph X-Server and return result
        metadata.

        This method issues a search request and extracts the session ID,
        result set number, and total number of matching records.

        Parameters
        ----------
        field : str
            Field code to search
            (e.g., "SYS" for system number, "BC" for barcode).
        value : str
            Query value to search for in the specified field.

        Returns
        -------
        tuple of (str, int)
            - `set_number`: Identifier for the result set.
            - `no_records`: Total number of records matching the query.

        Raises
        ------
        RuntimeError
            If the session ID is missing from the response.
        """
        response = self._session.get(
            f"{self._host}/{self._endpoint}",
            params={
                "op": XOperation.Search.value,
                "base": self._base,
                "code": field,
                "request": value,
            },
        )
        response.raise_for_status()

        content = etree.fromstring(response.content)
        session_id = content.findtext(".//session-id")

        if not session_id:
            error_message = content.findtext(".//h1") or "Unexpected response"
            raise RuntimeError(error_message)

        self._session.params["session_id"] = session_id

        set_number = content.findtext(".//set_number")
        no_records = int(content.findtext(".//no_records") or 0)

        return set_number, no_records

    def _fetch_results(
        self, set_number: str, page_start: int, page_end: int
    ) -> Generator[str, None, None]:
        """
        Fetch system numbers from a result set in the given page range.

        Parameters
        ----------
        set_number : str
            Identifier of the search result set.
        page_start : int
            First record index to retrieve (1-based).
        page_end : int
            Last record index to retrieve (inclusive).

        Yields
        ------
        str
            System numbers of the retrieved records.

        Raises
        ------
        requests.HTTPError
            If the HTTP request fails with a non-2xx status.
        """
        response = self._session.get(
            f"{self._host}/X",
            params={
                "op": XOperation.ListResults.value,
                "set_number": set_number,
                "set_entry": f"{page_start}-{page_end}",
            },
        )
        response.raise_for_status()

        content = etree.fromstring(response.content)
        self._session.params["session_id"] = content.findtext(".//session-id")

        for doc_number in content.findall(".//doc_number"):
            yield doc_number.text

    def find_system_numbers(
        self, field: str, value: str
    ) -> Generator[str, None, None]:
        """
        Search for system numbers by field and value, yielding all matches.

        This method performs a fielded search and paginates through the
        results, yielding each system number.

        Parameters
        ----------
        field : str
            Field code to search (e.g., "SYS", "BC").
        value : str
            Value to search for in the specified field.

        Yields
        ------
        str
            System numbers matching the search query.
        """
        set_number, no_records = self._search(field, value)

        for page in range(0, no_records, self._page_size):
            yield from self._fetch_results(
                set_number, page + 1, min(page + self._page_size, no_records)
            )

    def get_one_or_none_system_number(
        self, field: str, value: str
    ) -> str | None:
        """
        Return a single matching system number or None if not exactly one
        match.

        This method performs a fielded search and returns the system number
        only if the search yields exactly one result.

        Parameters
        ----------
        field : str
            Field code to search (e.g., "SYS", "BC").
        value : str
            Value to search for in the specified field.

        Returns
        -------
        str or None
            The system number if exactly one match is found; otherwise `None`.
        """
        set_number, no_records = self._search(field, value)

        if no_records != 1:
            return None

        results = list(self._fetch_results(set_number, 1, 1))
        return results[0] if results else None
