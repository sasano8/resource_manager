from typing import Type
from .abc import AbstractKVStore, Undefined
from .serializer import Serializer, JsonSerializer, YamlSerializer


class FilesystemKVStore(AbstractKVStore):
    def __init__(self, fs, serializer_cls: Type[Serializer]):
        import fsspec

        self._fs: fsspec.AbstractFileSystem = fsspec.filesystem("file://./")
        self._root = ""
        self._serializer_cls = serializer_cls

    def load(self, f):
        return self._serializer_cls.load(f)

    def dump(self, f):
        return self._serializer_cls.dump(f)

    def get(self, key, default=Undefined):
        opener = self._fs.open(key, "r")

        with opener as f:
            return self.load(f)

    def keys(self):
        for path in self._fs.find(self._root):
            yield path

    def values(self):
        for key, value in self.items():
            yield value

    def items(self):
        for key in self.keys():
            with self._fs.open(key, "r") as f:
                data = self.load(f)
            yield key, data
