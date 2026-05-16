import abc
import dataclasses

import httpx


@dataclasses.dataclass(frozen=True)
class AbstractAPIClient(abc.ABC):
    client: httpx.AsyncClient
