from .abc import AbstractKVStore, Undefined


class ArrayStore(AbstractKVStore):
    def __init__(self, stores: dict[str, AbstractKVStore]):
        self._stores = stores
