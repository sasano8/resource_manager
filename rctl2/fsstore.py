import fsspec

from .filesystems.utils import normalize_path
from .serializers import AbstractSerializer


def _from_fs(fs: fsspec.AbstractFileSystem, serializer: AbstractSerializer):
    paths = fs.find("", detail=False, withdirs=False)
    for path in paths:
        with fs.open(path) as f:
            yield path, serializer.load(f)


def flatten(data: dict, parent: str = ""):
    for k, v in data.items():
        key = parent + "/" + k if parent else k
        if isinstance(v, dict):
            yield from flatten(v)
        else:
            yield key, v


def normalize_keys(data: dict):
    for k, v in data.items():
        yield normalize_path(k), v


class DictStore:
    def __init__(self, data: dict):
        if not isinstance(data, dict):
            raise TypeError()
        self._data = dict(flatten(data))
        self._data = dict(normalize_keys(self._data))

    @classmethod
    def from_fs(cls, fs: fsspec.AbstractFileSystem, serializer: AbstractSerializer):
        return cls(dict(_from_fs(fs, serializer)))
