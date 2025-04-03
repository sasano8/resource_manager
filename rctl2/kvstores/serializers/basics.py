import json
import yaml
from .abc import AbstractSerializer


class MultiSerializer(AbstractSerializer):
    def __init__(self, serializers: dict[str, AbstractSerializer]):
        self._index: dict[str, AbstractSerializer] = serializers

    @classmethod
    def from_serializers(cls, *serializers: AbstractSerializer):
        index = {}
        for serializer in reversed(serializers):
            for ext in serializer.extensions:
                index[ext] = serializer
        return cls(index)

    def match(self, extension):
        serializer = self._index.get(extension, None)
        if serializer:
            return serializer
        else:
            return self._index.get("*", None)


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
    extensions = {"*"}

    def load(self, f):
        data = f.read()
        return data

    def dump(self, data, f):
        f.write(data)
