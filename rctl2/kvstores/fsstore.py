from .abc import AbstractKVStore, Undefined

import json
import yaml


class Serializer:
    @classmethod
    def load(cls, *args, **kwargs): ...

    @classmethod
    def dump(cls, *args, **kwargs): ...


class JsonSerializer(Serializer):
    load = json.load
    dump = json.dump


class YamlSerializer(Serializer):
    load = yaml.safe_load
    dump = yaml.safe_dump


class FilesystemKVStore(AbstractKVStore):
    def __init__(self, fs):
        import fsspec

        self._fs: fsspec.AbstractFileSystem = fsspec.filesystem("file://./")

    @classmethod
    def load(cls, f):
        return JsonSerializer.load(f)

    def get(self, key, default=Undefined):
        try:
            opener = self._fs.open(key, "r")
        except Exception as e:
            raise

        with opener as f:
            return self.load(f)
