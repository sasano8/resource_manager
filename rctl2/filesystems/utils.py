import os
import re

import fsspec

from ..serializers import (
    JsonSerializer,
    MultiSerializer,
    NullSerializer,
    TomlSerializer,
    YamlSerializer,
)

registry = MultiSerializer._make_registry(
    JsonSerializer, NullSerializer, TomlSerializer, YamlSerializer
)


def get_serializer(index: str, type: str, params: dict):
    serialize_cls = registry.get(type, None)
    if not serialize_cls:
        raise NotImplementedError(type)

    serializer = serialize_cls(**params)
    return index, serializer


def get_store(protocol, storage_options, root: str, loader):
    fs: fsspec.AbstractFileSystem = fsspec.filesystem(protocol, **storage_options)
    store = fs.get_mapper(root)
    data = dict(store)
    for k, v in data.items():
        ext = extract_ext(k)
        data[k] = loader(v, ext)

    return data


def extract_ext(path: str):
    _, ext = os.path.splitext(path)
    ext = ext.lstrip(".")
    return ext


def normalize_path(path: str):
    """パスを正規化する"""
    path = path.strip("/")
    path = re.sub(r"/+", "/", path)
    path = "/".join([x for x in path.split("/") if x != "." and x])
    return path
