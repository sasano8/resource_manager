class AbstractSerializer:
    extensions: set = set([])

    @classmethod
    def load(cls, f, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def dump(cls, data, f, *args, **kwargs):
        raise NotImplementedError()

    def match(self, extension):
        if extension in self.extensions:
            return self
        else:
            if "*" in self.extensions:
                return self
            else:
                return None
