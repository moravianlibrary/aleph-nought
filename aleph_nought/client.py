from .config import AlephConfig
from .oai import AlephOAIClient
from .x import AlephXClient
from .z3950 import AlephZ3950Client


class AlephClient:
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
