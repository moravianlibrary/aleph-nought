from enum import Enum


class OaiVerb(Enum):
    """
    OAI-PMH verbs as defined in the OAI-PMH specification.
    https://www.openarchives.org/OAI/openarchivesprotocol.html#ProtocolSyntax
    """

    GetRecord = "GetRecord"
    Identify = "Identify"
    ListIdentifiers = "ListIdentifiers"
    ListMetadataFormats = "ListMetadataFormats"
    ListRecords = "ListRecords"
    ListSets = "ListSets"


# ------------------------------------
# - XML Namespaces for OAI responses -
# ------------------------------------
NS_0 = {"ns0": "http://www.openarchives.org/OAI/2.0/"}
OAI_NS = {"oai": "http://www.openarchives.org/OAI/2.0/"}
MARC_NS = {"marc": "http://www.loc.gov/MARC21/slim"}
