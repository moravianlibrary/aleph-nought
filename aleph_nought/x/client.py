from typing import Generator, Tuple

from lxml import etree

from ..config import AlephXConfig
from ..web_client import AlephWebClient
from .custom_types import XOperation


class AlephXClient(AlephWebClient):
    def __init__(self, config: AlephXConfig):
        super().__init__(config)
        self._base = config.base
        self._page_size = config.page_size

    def is_available(self) -> bool:
        try:
            response = self._session.get(
                f"{self._host}/{self._endpoint}", params={"op": "ping"}
            )
            return response.status_code == 200
        except Exception:
            return False

    def _search(self, field: str, value: str) -> Tuple[str, int]:
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
        set_number, no_records = self._search(field, value)

        for page in range(0, no_records, self._page_size):
            yield from self._fetch_results(
                set_number, page + 1, min(page + self._page_size, no_records)
            )

    def get_one_or_none_system_number(
        self, field: str, value: str
    ) -> str | None:
        set_number, no_records = self._search(field, value)

        if no_records != 1:
            return None

        results = list(self._fetch_results(set_number, 1, 1))
        return results[0] if results else None
