import os

from ._dict import TextDictFileSystem


class EnvFileSystem(TextDictFileSystem):
    protocol = "env"

    def __init__(self, source: dict = None, skip_instance_cache: bool = False):
        if source is None:
            source = os.environ

        super().__init__(source, skip_instance_cache=skip_instance_cache)
