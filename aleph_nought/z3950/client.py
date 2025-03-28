from typing import List

from marcdantic import MarcRecord

from ..config import AlephZ3950Config
from .yaz_connectors import (
    destroy_connection,
    get_num_found,
    get_result_set_record,
    new_connection,
    search_pqf,
    set_connection_option,
)


class AlephZ3950Client:
    def __init__(self, config: AlephZ3950Config):
        self._host = config.host
        self._port = config.port
        self._session = new_connection(self._host, self._port)

        set_connection_option(self._session, "preferredRecordSyntax", "MARC21")
        set_connection_option(self._session, "databaseName", config.base)

    def close(self):
        if self._session:
            destroy_connection(self._session)
            self._session = None

    def __del__(self):
        self.close()

    def search(self, query: str) -> List[MarcRecord]:
        """Search for records. The base must return MARC21 in UTF-8 encoding

        Args:
            base (str): catalog base
            query (str): query in format PQF
                (https://software.indexdata.com/yaz/doc/tools.html)
        """
        result_set_p = search_pqf(self._session, query)

        return [
            get_result_set_record(result_set_p, i)
            for i in range(get_num_found(result_set_p))
        ]
