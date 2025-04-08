from io import StringIO
from os import environ

from ..serializers import AbstractSerializer
from .abc import AbstractKVStore, Undefined


class EnvStore(AbstractKVStore):
    def __init__(self, serializer: AbstractSerializer):
        self._serializer = serializer

    def open(self, path, *args, **kwargs):
        data = environ[path]
        return StringIO(data)

    def load(self, path):
        with self.open(path, "r") as f:
            return self._serializer.load(f)

    def dump(self, path):
        raise NotImplementedError()

    def exists(self, path: str):
        return path in environ

    def get(self, path: str, default=Undefined):
        if not self.exists(path):
            if default is not Undefined:
                return default
            else:
                raise KeyError(path)
        else:
            return self.load(path)

    def keys(self):
        yield from environ.keys()

    def values(self):
        for k, v in self.items():
            yield v

    def items(self):
        for (k,) in environ.keys():
            yield k, self.load(k)
