from os import environ

from ._dict import TextDictFileSystem


class EnvFileSystem(TextDictFileSystem):
    protocol = "env"

    def __init__(self, source: dict = None, cache: bool = True):
        if source is None:
            source = environ

        super().__init__(source, cache=cache)
