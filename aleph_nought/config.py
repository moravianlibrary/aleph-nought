from typing import List

from pydantic import BaseModel, Field, model_validator


class AlephWebConfig(BaseModel):
    """
    Base configuration for Aleph web clients (OAI, X).

    This configuration defines shared HTTP connection parameters used for
    communicating with Aleph endpoints.

    Attributes
    ----------
    host : str
        Base URL or hostname of the Aleph service.
    endpoint : str
        API or OAI-PMH endpoint path.
    timeout : int, default=30
        Request timeout in seconds.
    total_retry : int, default=5
        Maximum number of retries on connection or read failures.
    retry_backoff_factor : int, default=1
        Backoff factor applied between retry attempts.
    """

    host: str
    endpoint: str
    timeout: int = 30
    total_retry: int = 5
    retry_backoff_factor: int = 1


# TODO: Add validation for oai_identifier_template.
class AlephOAIConfig(AlephWebConfig):
    """
    Configuration for accessing Aleph's OAI-PMH service.

    Extends the base web configuration with OAI-specific parameters such as
    the identifier template, system number pattern, and set list.

    Attributes
    ----------
    base : str
        Aleph base code (e.g., "MZK01") used in identifiers.
    system_number_pattern : str
        Regular expression pattern for identifying system/document numbers.
    oai_sets : List[str], default=[]
        List of OAI set names to harvest from. Must contain at least one set.
    oai_identifier_template : str
        Template for generating OAI identifiers, containing `{base}` and
        `{doc_number}` placeholders.
    """

    base: str
    system_number_pattern: str
    oai_sets: List[str] = Field([], min_length=1)
    oai_identifier_template: str


class AlephXConfig(AlephWebConfig):
    """
    Configuration for accessing Aleph's X-Server.

    Attributes
    ----------
    base : str
        Aleph base code (e.g., "MZK01") for querying records.
    page_size : int, default=10
        Default number of records to fetch per request.
    """

    base: str
    page_size: int = 10


class AlephZ3950Config(BaseModel):
    """
    Configuration for accessing Aleph via the Z39.50 protocol.

    Attributes
    ----------
    host : str
        Hostname or IP address of the Z39.50 server.
    port : int
        Port number for the Z39.50 connection.
    base : str
        Aleph base code (e.g., "MZK01-UTF") used for Z39.50 queries.
    """

    host: str
    port: int
    base: str


class AlephConfig(BaseModel):
    """
    Top-level configuration container for all Aleph service clients.

    This model groups together the configurations for the OAI-PMH, X-Server,
    and Z39.50 services. At least one service configuration must be provided.

    Attributes
    ----------
    base : str
        Common Aleph base code (e.g., "MZK01").
    oai : AlephOAIConfig or None, default=None
        Configuration for the OAI-PMH service.
    x : AlephXConfig or None, default=None
        Configuration for the Aleph X-Server.
    z3950 : AlephZ3950Config or None, default=None
        Configuration for the Z39.50 protocol.

    Raises
    ------
    ValueError
        If none of the OAI, X, or Z39.50 configurations are defined.

    Notes
    -----
    This model uses a post-initialization validator to enforce the presence
    of at least one service configuration.
    """

    base: str

    oai: AlephOAIConfig | None = None
    x: AlephXConfig | None = None
    z3950: AlephZ3950Config | None = None

    @model_validator(mode="after")
    def validate_config(cls, config: "AlephConfig") -> None:
        if not any([config.oai, config.x, config.z3950]):
            raise ValueError(
                "At least one of the Aleph services must be configured"
            )
