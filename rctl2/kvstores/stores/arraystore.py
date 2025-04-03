from .abc import AbstractKVStore, Undefined


class ArrayStore(AbstractKVStore):
    def __init__(self, stores: list[AbstractKVStore]):
        self._stores = stores
