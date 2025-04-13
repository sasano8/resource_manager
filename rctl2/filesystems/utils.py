import os
import re

import fsspec


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
