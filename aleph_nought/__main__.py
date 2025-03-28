from .client import AlephClient
from .config import AlephConfig, AlephOAIConfig, AlephXConfig, AlephZ3950Config

client = AlephClient(
    AlephConfig(
        base="MZK01",
        oai=AlephOAIConfig(
            host="https://aleph.mzk.cz", endpoint="OAI", base="MZK01"
        ),
        x=AlephXConfig(
            host="https://aleph.mzk.cz", endpoint="X", base="MZK01"
        ),
        z3950=AlephZ3950Config(host="aleph.mzk.cz", port=9991, base="MZK01"),
    )
)


print(client.OAI.is_available())
print(client.X.is_available())
print(client.Z3950.is_available())

record = client.OAI.get_record("MZK01", "000960080")
record = client.OAI.get_record("MZK01", "000140633")
record = client.OAI.get_record("MZK01", "001196849")

print(
    list(
        client.OAI.list_records(
            "MZK01-VDK", "2025-03-01T16:15:40Z", "2025-03-07T18:15:40Z"
        )
    )
)
