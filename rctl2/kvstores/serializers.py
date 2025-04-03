import json
import yaml


class Serializer:
    extensions: set = set([])

    @classmethod
    def load(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def dump(cls, *args, **kwargs):
        raise NotImplementedError()

    def match(self, extension):
        if extension in self.extensions:
            return self
        else:
            return None


class MultiSerializer(Serializer):
    def __init__(self, serializers: dict[str, Serializer]):
        self._index = serializers

    @classmethod
    def from_serializers(cls, *serializers):
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


class JsonSerializer(Serializer):
    extensions = {"json"}
    load = json.load
    dump = json.dump


class YamlSerializer(Serializer):
    extensions = {"yaml", "yml"}
    load = yaml.safe_load
    dump = yaml.safe_dump


class TextSerializer(Serializer):
    extensions = {"txt"}

    def load(self, f):
        data = f.read()
        return data

    def dump(self, data, f):
        f.write(data)
