import json
from io import BytesIO, StringIO

import fsspec


def extract_erros(items, parent_key: str = ""):
    messages = {}

    for k, v in items:
        key = parent_key + "/" + k if parent_key else k
        if isinstance(v, dict):
            yield from extract_erros(v.items(), key)
        else:
            if not isinstance(v, (str, bytes)):
                messages.setdefault(key, []).append(
                    "The value must be either str or bytes."
                )

    yield from messages.items()


class TextDictFileSystem(fsspec.AbstractFileSystem):
    protocol = None  # 登録しない

    def __init__(self, data: dict, skip_instance_cache: bool = False):
        self._data: dict = data

        errors = dict(extract_erros(self._data.items()))
        if errors:
            raise ValueError(errors)

        # skip_instance_cache = True は、filesystem インスタンスを取得する時にオブジェクトをキャッシュする
        # 基本的に無効でよい
        super().__init__(skip_instance_cache=skip_instance_cache)

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
        self,
        path: str,
        mode: str = "rb",
        block_size: int | None = None,
        encoding: str = "utf-8",
        **kwargs,
    ):
        if path not in self._data:
            raise FileNotFoundError(path)

        data = self._data[path]

        if mode == "r":
            if isinstance(data, bytes):
                data = data.decode(encoding)

            f = StringIO()
            json.dump(data, f)
            f.seek(0)
            return f

        elif mode == "rb":
            if isinstance(data, bytes):
                data = data.decode(encoding)

            f = BytesIO(json.dumps(data).encode(encoding))
            f.seek(0)
            return f

        else:
            raise ValueError(
                f"Unsupported mode: {mode}. Supported modes are 'r', 'rb', 'w', 'wb'"
            )
