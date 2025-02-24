from ..base import Resource
from pathlib import Path
import fsspec
from fsspec import AbstractFileSystem


class FileManager(Resource):
    def __init__(self, path: str, content: str = ""):
        self._path = Path(path)
        self._content = content

    def create(self):
        with self._path.open("x") as f:
            f.write(self._content)
        return True, ""

    def delete(self):
        self._path.unlink(missing_ok=True)
        return True, ""

    def exists(self):
        if self._path.exists():
            return True, ""
        else:
            return False, f"Not Exists {str(self._path)}"

    def absent(self):
        if self._path.exists():
            return False, f"Exists {str(self._path)}"
        else:
            return True, ""


class FsspecOperator(Resource):
    def __init__(self, protocol, **kwargs):
        self._protocol = protocol
        self._kwargs = kwargs

    def get_filesystem(self) -> AbstractFileSystem:
        return fsspec.filesystem(self._protocol, **self._kwargs)

    def create(self, path: str, content: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        directory = "/".join(path.split("/")[:-1])
        if not fs.exists(directory):
            fs.mkdirs(directory, exist_ok=True)

        with fs.open(path, "x") as f:
            f.write(content)
        return True, ""

    def delete(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        fs.delete(path, recursive=True)
        return True, ""

    def exists(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        if fs.exists(path):
            return True, ""
        else:
            return False, f"Not Exists {str(path)}"

    def absent(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        if fs.exists(path):
            return False, f"Exists {str(path)}"
        else:
            return True, ""
