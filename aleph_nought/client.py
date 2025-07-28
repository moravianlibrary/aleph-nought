from typing import List, Mapping

from .config import AlephConfig
from .oai import AlephOAIClient
from .x import AlephXClient
from .z3950 import AlephZ3950Client


class AlephClient:
    """
    Unified client for accessing multiple Aleph services.

    This class acts as a facade over the individual Aleph service clients:
    OAI, X-Server, and Z39.50, providing convenient access to each
    configured service.

    Parameters
    ----------
    config : AlephConfig
        Configuration object specifying which Aleph services to enable
        and their connection details.

    Attributes
    ----------
    OAI : AlephOAIClient
        Client for the Aleph OAI-PMH service.
        Raises ValueError if not configured.
    X : AlephXClient
        Client for the Aleph X-Server service.
        Raises ValueError if not configured.
    Z3950 : AlephZ3950Client
        Client for the Aleph Z39.50 service.
        Raises ValueError if not configured.
    """

    def __init__(self, config: AlephConfig):
        if config.oai:
            self._oai = AlephOAIClient(config.oai)
        if config.x:
            self._x = AlephXClient(config.x)
        if config.z3950:
            self._z3950 = AlephZ3950Client(config.z3950)

    @property
    def OAI(self) -> AlephOAIClient:
        if not self._oai:
            raise ValueError("OAI service is not configured")
        return self._oai

    @property
    def X(self) -> AlephXClient:
        if not self._x:
            raise ValueError("X service is not configured")
        return self._x

    @property
    def Z3950(self) -> AlephZ3950Client:
        if not self._z3950:
            raise ValueError("Z3950 service is not configured")
        return self._z3950


def build_aleph_client_map(
    config: List[AlephConfig],
) -> Mapping[str, AlephClient]:
    """
    Build a mapping from Aleph base codes to AlephClient instances.

    Parameters
    ----------
    config : List[AlephConfig]
        List of AlephConfig objects, each describing a single Aleph base and
        its enabled services.

    Returns
    -------
    Mapping[str, AlephClient]
        Dictionary mapping each Aleph base code to a configured AlephClient.

    Raises
    ------
    ValueError
        If duplicate base codes are found in the provided configuration list.
    """
    clients = {}
    for cfg in config:
        if cfg.base in clients:
            raise ValueError(f"Duplicate Aleph base: {cfg.base}")
        clients[cfg.base] = AlephClient(cfg)
    return clients
