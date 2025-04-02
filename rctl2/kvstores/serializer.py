import json
import yaml


class Serializer:
    @classmethod
    def load(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def dump(cls, *args, **kwargs):
        raise NotImplementedError()


class JsonSerializer(Serializer):
    load = json.load
    dump = json.dump


class YamlSerializer(Serializer):
    load = yaml.safe_load
    dump = yaml.safe_dump
