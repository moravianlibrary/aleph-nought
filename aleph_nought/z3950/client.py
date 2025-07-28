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
    """
    Client for interacting with Aleph via the Z39.50 protocol using
    the YAZ library.

    This client establishes a connection to an Aleph Z39.50 server, executes
    PQF queries, and retrieves MARC21 records encoded in UTF-8.

    The implementation uses the YAZ C++ library with Python bindings for
    connection management, querying, and result retrieval.
    The documentation for YAZ can be found here:
    https://www.indexdata.com/resources/software/yaz/

    Parameters
    ----------
    config : AlephZ3950Config
        Configuration object containing host, port, and database base name.

    Methods
    -------
    close()
        Closes the active Z39.50 connection.
    search(query: str) -> List[MarcRecord]
        Executes a PQF query string and returns a list of MARC records.

    Notes
    -----
    - The query format must comply with PQF (Prefix Query Format):
      https://software.indexdata.com/yaz/doc/tools.html
    - The base database must return records in MARC21 UTF-8 encoding.
    - Proper resource cleanup is performed on object deletion.
    """

    def __init__(self, config: AlephZ3950Config):
        self._host = config.host
        self._port = config.port
        self._session = new_connection(self._host, self._port)

        set_connection_option(self._session, "preferredRecordSyntax", "MARC21")
        set_connection_option(self._session, "databaseName", config.base)

    def close(self):
        """
        Close the active Z39.50 connection.

        Safely destroys the current connection session if it exists,
        freeing associated resources.
        """
        if self._session:
            destroy_connection(self._session)
            self._session = None

    def __del__(self):
        self.close()

    def search(self, query: str) -> List[MarcRecord]:
        """
        Search the Aleph Z39.50 server using a PQF query and
        return MARC21 records.

        Parameters
        ----------
        query : str
            Query string formatted according to the Prefix Query Format (PQF).
            See https://software.indexdata.com/yaz/doc/tools.html for details.

        Returns
        -------
        List[MarcRecord]
            List of MARC records retrieved from the server matching the query.

        Notes
        -----
        - The database specified in the configuration must support MARC21
          records encoded in UTF-8.
        - Uses the YAZ library bindings to communicate with the server.
        """
        result_set_p = search_pqf(self._session, query)

        return [
            get_result_set_record(result_set_p, i)
            for i in range(get_num_found(result_set_p))
        ]
