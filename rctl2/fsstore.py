from typing import Any

import fsspec
from fsspec.implementations.dirfs import DirFileSystem

from .filesystems.utils import normalize_path
from .serializers import AbstractSerializer

"""env1:
    store:
        type: env
    serializer:
        type: null
    params:
        root: ""
        prefix: ""

env2:
    store:
        type: fsspec
    serializer:
        type: yaml
    params:
        root: ""

env3:
    store:
        type: dict
        params:
            src: "env2"  # 別のストアをソースとして参照可能（キャッシュとして機能）
    serializer:
        type: null
"""


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


# from .abc import AbstractKVStore, Undefined


class AbstractKVStore: ...


Undefined = object()


class DictKVStore(AbstractKVStore):
    def __init__(self, data: dict):
        if not isinstance(data, dict):
            raise TypeError()

        self._data = data

    def keys(self):
        yield from (k for k, v in self.items())

    def values(self):
        yield from (v for k, v in self.items())

    def items(self):
        def _iter(parent, items: dict):
            for k, v in items.items():
                if parent:
                    current = parent + "/" + k
                else:
                    current = k

                if isinstance(v, dict):
                    yield from _iter(current, v)
                else:
                    yield current, v

        yield from _iter("", self._data)

    def get(self, path: str, default=Undefined):
        for k, v in self.items():
            if path == k:
                return v

        if default is Undefined:
            raise KeyError(path)
        else:
            return default


class FileStore(AbstractKVStore):
    def __init__(self, fs: DirFileSystem, dumper, loader):
        self._fs = fs
        self._dumper = dumper
        self._loader = loader

        if not isinstance(fs, DirFileSystem):
            raise RuntimeError()

    @classmethod
    def create(cls, fs, root, serializer=None, loader=None, dumper=None):
        _loader = None
        _dumper = None

        if serializer:
            _loader = getattr(serializer, "load", None)
            _dumper = getattr(serializer, "dump", None)

        if loader:
            _loader = loader

        if dumper:
            _dumper = dumper

        raise NotImplementedError

    def open(self, *args, **kwargs):
        return self._fs.open(*args, **kwargs)

    def load(self, path):
        with self.open(path, "r") as f:
            return self._loader(f)

    def dump(self, path):
        with self.open(path, "w") as f:
            return self._dumper(f)

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

    def to_dict(self, sep: str = "/", map=None) -> dict[str, Any]:
        map = map or (lambda x: x)
        return {map(k.replace("/", sep)): v for k, v in self.items()}
