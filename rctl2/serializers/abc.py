from typing import TYPE_CHECKING


class AbstractSerializer:
    extensions: set = set([])

    def loads(self, s, extension="", *args, **kwargs):
        raise NotImplementedError()

    def dumps(self, s, extension="", *args, **kwargs):
        raise NotImplementedError()

    def match(self, extension):
        if extension in self.extensions:
            return self
        else:
            if "*" in self.extensions:
                return self
            else:
                return None
