import fsspec


class ArrayFileSystem:
    def __init__(self, filesystems: dict[str, fsspec.AbstractFileSystem]):
        self._filesystems = filesystems

    @classmethod
    def from_dict(cls, data: dict[str, dict]):
        def instantiate(items: dict):
            for k, v in items.items():
                dir = v.get("dir", "")  # noqa
                params = v["params"]
                yield k, fsspec.filesystem(**params)

        return cls(dict(instantiate(data)))

    def get_mountpoint(self, path):
        return self._filesystems[path]
