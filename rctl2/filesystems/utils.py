import re


def normalize_path(path: str):
    """パスを正規化する"""
    path = path.strip("/")
    path = re.sub(r"/+", "/", path)
    path = "/".join([x for x in path.split("/") if x != "." and x])
    return path
