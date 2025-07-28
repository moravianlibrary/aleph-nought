from enum import Enum


class RecordStatus(Enum):
    """
    Enumeration of possible statuses for a record in the Aleph system.

    Attributes
    ----------
    Active : str
        Indicates the record is active and available.
    Deleted : str
        Indicates the record has been deleted.
    Failed : str
        Indicates the record failed processing or retrieval.
    """

    Active = "Active"
    Deleted = "Deleted"
    Failed = "Failed"
