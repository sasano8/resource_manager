import json
import yaml
from .abc import AbstractSerializer


class MultiSerializer(AbstractSerializer):
    def __init__(self, serializers: dict[str, AbstractSerializer]):
        self._index = serializers

    @classmethod
    def from_serializers(cls, *serializers: AbstractSerializer):
        index = {}
        for serializer in serializers:
            for ext in serializer.extensions:
                index[ext] = serializer
        return cls(index)

    def match(self, extension):
        return self._index.get(extension, None)

    def load_by_ext(self, ext, *args, **kwargs):
        serializer = self.match(ext)
        if not serializer:
            raise NotImplementedError()

        return serializer.load(*args, **kwargs)

    def dump_by_ext(self, ext, *args, **kwargs):
        serializer = self.match(ext)
        if not serializer:
            raise NotImplementedError()

        return serializer.dump(*args, **kwargs)


class JsonSerializer(AbstractSerializer):
    extensions = {"json"}
    load = staticmethod(json.load)
    dump = staticmethod(json.dump)


class YamlSerializer(AbstractSerializer):
    extensions = {"yaml", "yml"}
    load = staticmethod(yaml.safe_load)
    dump = staticmethod(yaml.safe_dump)


class TomlSerializer(AbstractSerializer): ...


class NullSerializer(AbstractSerializer):
    extensions = {"txt"}

    def load(self, f):
        data = f.read()
        return data

    def dump(self, data, f):
        f.write(data)
