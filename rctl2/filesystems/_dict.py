from io import BytesIO, StringIO

import fsspec


class DictFileSystem(fsspec.AbstractFileSystem):
    protocol = None  # 登録しない

    def __init__(self, data: dict, cache: bool = True):
        if cache:
            self._data: dict = dict(data)
        else:
            self._data: dict = data

    def info(self, path):
        if path not in self._data:
            raise FileNotFoundError(path)

        return {"name": path, "size": None, "type": "file"}

    def exists(self, path):
        return path in self._data

    def ls(self, path: str, detail: bool = True, **kwargs):
        if not path:
            if detail:
                return list(self.info(x) for x in self._data.keys())
            else:
                return list(self._data.keys())
        else:
            return []

    def find(self, path: str, maxdepth=None, withdirs=False, detail=False):
        if path:
            return []
        else:
            return self.ls(path, detail=detail)

    def open(
        self, path: str, mode: str = "rb", block_size: int | None = None, **kwargs
    ):
        if mode == "r":
            if path in self._data:
                return StringIO(self._data[path])
            else:
                raise FileNotFoundError(path)
        elif mode == "rb":
            if path in self._data:
                return BytesIO(self._data[path].encode("UTF8"))
            else:
                raise FileNotFoundError(path)
        else:
            raise ValueError(
                f"Unsupported mode: {mode}. Supported modes are 'r', 'rb', 'w', 'wb'"
            )
