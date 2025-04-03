from .abc import AbstractKVStore, Undefined


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
