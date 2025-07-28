from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AlephWebConfig


class AlephWebClient:
    """
    Base client for interacting with Aleph web services via HTTP.

    This client manages HTTP sessions with built-in retry logic for robustness,
    handling retries on specified HTTP status codes with exponential backoff.

    Parameters
    ----------
    config : AlephWebConfig
        Configuration object containing host URL, endpoint path,
        timeout settings, and retry parameters.

    Methods
    -------
    close()
        Closes the HTTP session.
    """

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
        """
        Close the HTTP session managed by this client.

        This method releases any network resources held by the session.
        It is recommended to call this method when the client is no longer
        needed to ensure proper cleanup of connections.
        """
        if self._session:
            self._session.close()

    def __del__(self):
        self.close()
