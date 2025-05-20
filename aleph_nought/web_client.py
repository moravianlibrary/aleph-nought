from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AlephWebConfig


class AlephWebClient:
    def __init__(self, config: AlephWebConfig):
        self._host = config.host.strip("/")
        self._endpoint = config.endpoint
        self._session = Session()
        self._session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=config.total_retry,
                    backoff_factor=config.retry_backoff_factor,
                    status_forcelist=[500, 502, 503, 504],
                )
            ),
        )
        self._session.timeout = config.timeout

    def close(self):
        if self._session:
            self._session.close()

    def __del__(self):
        self.close()
