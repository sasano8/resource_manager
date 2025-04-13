import json
import tomllib

import yaml

from .abc import AbstractSerializer


class MultiSerializer(AbstractSerializer):
    extensions = {""}

    def __init__(self, serializers: dict[str, AbstractSerializer]):
        self._index: dict[str, AbstractSerializer] = serializers

    @classmethod
    def _make_index(cls, *serializers: AbstractSerializer):
        index = {}
        for serializer in reversed(serializers):
            for ext in serializer.extensions:
                index[ext] = serializer
        return index

    @classmethod
    def from_serializers(cls, *serializers: AbstractSerializer):
        index = cls._make_index(*serializers)
        return cls(index)

    def match(self, extension):
        serializer = self._index.get(extension, None)
        if serializer:
            return serializer
        else:
            return self._index.get("*", None)

    def loads(self, s, extension="", *args, **kwargs):
        serializer = self.match(extension)
        if not serializer:
            raise NotImplementedError(f"No match extension: {extension}")

        return serializer.loads(s, *args, **kwargs)

    def dumps(self, data, extension="", *args, **kwargs):
        serializer = self.match(extension)
        if not serializer:
            raise NotImplementedError(f"No match extension: {extension}")

        return serializer.dumps(data, *args, **kwargs)


class JsonSerializer(AbstractSerializer):
    extensions = {"json"}

    def loads(self, s, extension="", *args, **kwargs):
        return json.loads(s)

    def dumps(self, data, extension="", *args, **kwargs):
        return json.dumps(data, ensure_ascii=False)


class YamlSerializer(AbstractSerializer):
    extensions = {"yaml", "yml"}

    def loads(self, s, extension="", *args, **kwargs):
        return yaml.safe_load(s)

    def dumps(self, s, extension="", *args, **kwargs):
        return yaml.safe_dump(s)


class TomlSerializer(AbstractSerializer):
    extensions = {"toml"}

    def loads(self, s, extension="", *args, **kwargs):
        return tomllib.loads(s)

    def dumps(self, s, extension="", *args, **kwargs):
        raise NotImplementedError()


# class StrSerializer(AbstractSerializer):
#     extensions = {"text"}

#     def load(self, f):
#         _data = f.read()
#         if isinstance(_data, bytes):
#             _data = _data.decode("utf-8")

#         if not isinstance(_data, str):
#             raise ValueError()

#         return _data

#     def dump(self, data, f):
#         _data = data
#         if isinstance(data, bytes):
#             _data = data.decode("utf-8")

#         if not isinstance(_data, str):
#             raise ValueError()

#         f.write(_data)


# class BytesSerializer(AbstractSerializer):
#     extensions = {"bin"}

#     def load(self, f):
#         _data = f.read()
#         if isinstance(_data, str):
#             _data = _data.encode("utf-8")

#         if not isinstance(_data, bytes):
#             raise ValueError()

#         return _data

#     def dump(self, data, f):
#         _data = data
#         if isinstance(data, str):
#             _data = data.encode("utf-8")

#         if not isinstance(_data, bytes):
#             raise ValueError()

#         f.write(_data)


class NullSerializer(AbstractSerializer):
    extensions = {"null"}

    def loads(self, s, extension="", *args, **kwargs):
        return s

    def dumps(self, s, extension="", *args, **kwargs):
        return s
