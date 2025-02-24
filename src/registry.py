from . import modules as mo
from .base import HasOperator

class Registry:
    """Manifest と type をマッピングする"""

    def __init__(self, map: dict[str, HasOperator] = {}):
        self._map = map

    def get_cls(self, type: str):
        t = self._map.get(type, None)
        return t


_registry = Registry(
    {"true": mo.TrueResource, "false": mo.TrueResource, "fsspec": mo.FsspecRootOperator}
)
