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
    {
        "true": mo.TrueOperator,
        "false": mo.TrueOperator,
        "fsspec": mo.FsspecRootOperator,
        "psycopg2": mo.Psycopg2SchemaOperator,
        "boto3": mo.Boto3Controller,
    }
)
