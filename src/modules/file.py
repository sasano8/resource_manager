from ..base import Operator
import fsspec
from fsspec import AbstractFileSystem


class FsspecRootOperator(Operator):
    @staticmethod
    def get_operator(type: str):
        if type == "file":
            return FsspecFileOperator
        elif type == "dir":
            return FsspecDirOperator
        else:
            raise TypeError()


class FsspecFileOperator(Operator):
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
            if fs.isfile(path):
                return True, ""
            else:
                return False, f"Not File."
        else:
            return False, f"Not Exists {str(path)}"

    def absent(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        if fs.exists(path):
            return False, f"Exists {str(path)}"
        else:
            return True, ""


class FsspecDirOperator(Operator):
    def __init__(self, protocol, **kwargs):
        self._protocol = protocol
        self._kwargs = kwargs

    def get_filesystem(self) -> AbstractFileSystem:
        return fsspec.filesystem(self._protocol, **self._kwargs)

    def create(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        if not fs.exists(path):
            fs.mkdirs(path, exist_ok=True)
        return True, ""

    def delete(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        fs.rmdir(path)
        # fs.rm(path, recursive=True)
        return True, ""

    def exists(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        if fs.exists(path):
            if fs.isdir(path):
                return True, ""
            else:
                return False, f"Not directory."
        else:
            return False, f"Not Exists {str(path)}"

    def absent(self, path: str, *args, **kwargs):
        fs = self.get_filesystem()
        if fs.exists(path):
            return False, f"Exists {str(path)}"
        else:
            return True, ""
