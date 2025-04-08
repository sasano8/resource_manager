import json
from os import environ


class Error(Exception):
    def __bool__(self):
        return False


protocols = {"memory", "env", "local"}


def to_json(v):
    if not v:
        return None
    else:
        return json.loads(v)


def kvstore(protocol, option={}):
    if protocol == "memory":
        raise NotImplementedError()
    elif protocol == "env":
        raise NotImplementedError()
    elif protocol == "file":
        raise NotImplementedError()
    else:
        raise NotImplementedError()


class LocalEnvKVStore:
    def __init__(self, prefix: str = "", variables: dict = {}):
        self._store = environ
        self._prefix = prefix.replace("/", "_")

        if self._prefix:
            if self._prefix[-1] != "_":
                self._prefix = self._prefix + "_"

        for k, v in variables.items():
            self.set(k, v)

    @classmethod
    def get_protocol(cls):
        return "env"

    def get(self, key: str):
        newkey = self._prefix + key.replace("/", "_")
        return to_json(self._store.get(newkey))

    def set(self, key: str, value):
        newkey = self._prefix + key.replace("/", "_")
        dumped = json.dumps(value)
        self._store[newkey] = dumped

    def keys(self):
        s = self._store
        p = self._prefix
        for k in s.keys():
            if p in k:
                yield k

    def items(self):
        for k, v in self._store.items():
            yield k, v

    def dump(self):
        return {
            "type": self.get_protocol(),
            "prefix": self._prefix,
            "variables": dict(self.items()),
        }

    @classmethod
    def load_from_path(cls, path):
        with open(path) as f:
            data = json.load(f)
            return cls.load(data)

    @classmethod
    def load(cls, data: dict):
        return cls(**data)


class FileKVStore:
    """ファイルシステム上の .yml ファイルを変数として扱う Key Value Store"""

    ...
