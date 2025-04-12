import os
from typing import Any, BinaryIO, TextIO

import fsspec


def split_path(path: str):
    args = [x for x in path.strip("/").split("/") if x]
    args = args or [""]
    first, others = args[0], args[1:]
    return first, "/".join(others)


def normalize_path(path: str):
    return path.replace("//", "/")


class ArrayFileSystem(fsspec.AbstractFileSystem):
    protocol = "array"

    def __init__(self, filesystems: dict[str, dict]):
        self._filesystems: dict[str, fsspec.AbstractFileSystem] = self._from_dict(
            filesystems
        )

    @classmethod
    def _from_dict(cls, data: dict[str, dict]):
        def instantiate(items: dict):
            for k, v in items.items():
                # dir = v.get("dir", "")  # noqa
                # params = v.get("params", {})
                params = v
                yield k, fsspec.filesystem(**params)

        return dict(instantiate(data))

    def exists(self, path: str) -> bool:
        first, others = split_path(path)
        if not others:
            return first in self._filesystems
        else:
            fs = self._filesystems.get(first, None)
            if fs:
                return fs.exists(others)
            else:
                return False

    def open(self, path: str, mode: str = "rb", **kwargs) -> BinaryIO | TextIO:
        first, others = split_path(path)
        fs = self._filesystems.get(first, None)
        if not fs:
            raise FileNotFoundError(path)

        return fs.open(others, mode=mode, **kwargs)

    def _ls(self, path: str, detail: bool = True, **kwargs):
        first, others = split_path(path)
        if not first:
            if detail:
                for k in self._filesystems.keys():
                    yield {"name": k}
            else:
                yield from self._filesystems.keys()
        else:
            fs = self._filesystems.get(first, None)
            if not fs:
                return
            if detail:
                for data in fs.ls(others, detail=detail):
                    data["name"] = normalize_path("/".join([first, data["name"]]))
                    yield data
            else:
                for k in fs.ls(others, detail=detail):
                    yield normalize_path("/".join([first, k]))

    def ls(self, path: str, detail: bool = True, **kwargs) -> list[str] | list[dict]:
        return list(self._ls(path, detail=detail, **kwargs))

    def _find(self, path: str, maxdepth=None, withdirs=False, detail=False):
        first, others = split_path(path)
        if not others:
            yield from (x for x in self.ls(first, detail=detail))
        else:
            if not first:
                yield from self.ls(first, detail=detail)
            else:
                fs = self._filesystems.get(first, None)
                if not fs:
                    yield from []
                else:
                    if detail:
                        for x in fs.find(
                            others, maxdepth=maxdepth, withdirs=withdirs, detail=detail
                        ):
                            x["name"] = normalize_path("/".join([first, x["name"]]))
                            yield x
                    else:
                        for x in fs.find(
                            others, maxdepth=maxdepth, withdirs=withdirs, detail=detail
                        ):
                            x = "/".join([first, x])
                            yield normalize_path(x)

    def find(self, path: str, maxdepth=None, withdirs=False, detail=False):
        return list(
            self._find(path, maxdepth=maxdepth, withdirs=withdirs, detail=detail)
        )

    def info(self, path: str) -> dict[str, Any]:
        first, others = split_path(path)
        if not first:
            raise FileNotFoundError()

        if not others:
            fs = self._filesystems.get(first, None)
            if fs:
                return {"name": first, "type": "dir"}
            else:
                raise FileNotFoundError(first)
        else:
            fs = self._filesystems.get(first, None)
            if fs:
                info = fs.info(others)
                info["name"] = "/".join([first, info["name"]])
            else:
                raise FileNotFoundError(first)

    def rm(self, path: str, recursive: bool = False, **kwargs):
        raise NotImplementedError()
