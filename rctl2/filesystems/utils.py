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


def get_store(protocol, storage_options, root: str, loader):
    fs: fsspec.AbstractFileSystem = fsspec.filesystem(protocol, **storage_options)
    store = fs.get_mapper(root)
    data = dict(store)
    for k, v in data.items():
        ext = extract_ext(k)
        data[k] = loader(v, ext)

    return data


def get_store_from_dict(protocol, storage_options, root: str, loader: dict):
    index = {}
    for k, v in loader.items():
        type = v["type"]
        params = v.get("params", {})
        serialize_cls = registry.get(type, None)
        if not serialize_cls:
            raise NotImplementedError(type)

        serializer = serialize_cls(**params)
        index[k] = serializer

    serializer = MultiSerializer(index)
    return get_store(
        protocol, storage_options=storage_options, root=root, loader=serializer.loads
    )


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
