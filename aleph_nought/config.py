from pydantic import BaseModel, model_validator


class AlephWebConfig(BaseModel):
    host: str
    endpoint: str
    timeout: int = 30
    total_retry: int = 5
    retry_backoff_factor: int = 1


class AlephOAIConfig(AlephWebConfig):
    base: str


class AlephXConfig(AlephWebConfig):
    base: str
    page_size: int = 10


class AlephZ3950Config(BaseModel):
    host: str
    port: int
    base: str


class AlephConfig(BaseModel):
    base: str

    oai: AlephOAIConfig | None = None
    x: AlephXConfig | None = None
    z3950: AlephZ3950Config | None = None

    @model_validator(mode="before")
    def validate_config(cls, config: "AlephConfig") -> None:
        if not any([config.oai, config.x, config.z3950]):
            raise ValueError(
                "At least one of the Aleph services must be configured"
            )
