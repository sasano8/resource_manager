from .serializers import Serializer
from fsspec.implementations.dirfs import DirFileSystem
from .abc import Undefined


class FileHandler:
    def __init__(self, fs: DirFileSystem, serializer_cls: Serializer):
        self._fs = fs
        self._serializer_cls = serializer_cls

        if not isinstance(fs, DirFileSystem):
            raise RuntimeError()

    @classmethod
    def create(cls, _serializer_cls, fs, root):
        raise NotImplementedError

    def open(self, *args, **kwargs):
        return self._fs.open(*args, **kwargs)

    def load(self, path):
        with self.open(path, "r") as f:
            return self._serializer_cls.load(f)

    def dump(self, path):
        with self.open(path, "w") as f:
            return self._serializer_cls.dump(f)

    def keys(self):
        for path in self._fs.find("", detail=False):
            yield path

    def values(self):
        for k, v in self.items():
            yield v

    def items(self):
        for key in self.keys():
            data = self.load(key)
            yield key, data

    def exists(self, path: str):
        return self._fs.exists(path)

    def get(self, path: str, default=Undefined):
        if not self.exists(path):
            if default is not Undefined:
                return default
            else:
                raise KeyError(path)
        else:
            return self.load(path)
