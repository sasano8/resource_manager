from os import environ

from ._dict import DictFileSystem


class EnvFileSystem(DictFileSystem):
    protocol = "env"

    def __init__(self, source: dict = None, cache: bool = True):
        if source is None:
            source = environ

        super().__init__(source, cache=cache)
