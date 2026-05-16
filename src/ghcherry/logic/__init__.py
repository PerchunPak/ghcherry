from ._cherry_picker import CherryPicker
from ._misc import MiscAPIClinent
from ._pr import PRApiClient

__all__ = ["APIClient"]


class APIClient(
    CherryPicker,
    MiscAPIClinent,
    PRApiClient,
):
    pass
