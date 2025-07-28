from enum import Enum


class XOperation(Enum):
    """
    Enum representing supported operations of the Aleph X-Server API.

    Each member corresponds to a specific operation keyword used
    in requests to the Aleph X-Server.

    For detailed information on these operations, see the official
    Aleph X-Server API documentation:
    https://developers.exlibrisgroup.com/aleph/apis/aleph-x-services/
    """

    Ping = "ping"
    Search = "find"
    ListResults = "present"
