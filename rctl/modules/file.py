from ..base import Operator
import fsspec
from fsspec import AbstractFileSystem
from os import path as pathutil


unsafes = {"~", "..", "*", "{", "}"}
bucket_unsafes = {"/"}


def safe_join(bucket, *args):
    """s3 のバケット命名規約に従わせる。あと、endpoint にバケット名を含めることができるが、挙動を制御できないので禁止させること"""
    if not bucket:
        raise ValueError(bucket)
    return pathutil.join(bucket, *args)


class FsspecRootOperator(Operator):
    def __init__(self, protocol, **kwargs):
        self._protocol = protocol
        self._kwargs = kwargs

    def get_filesystem(self) -> AbstractFileSystem:
        return fsspec.filesystem(self._protocol, **self._kwargs)

    @staticmethod
    def get_operator(type: str):
        if type == "file":
            return FsspecFileOperator
        elif type == "dir":
            return FsspecDirOperator
        elif type == "bucket":
            return FsspecBucketOperator
        else:
            raise TypeError()


class FsspecFileOperator(FsspecRootOperator):
    def create(self, path: str, bucket: str = "", content: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        directory = "/".join(p.split("/")[:-1])
        if not fs.exists(directory):
            fs.mkdirs(directory, exist_ok=True)

        with fs.open(p, "x") as f:
            f.write(content)
        return True, ""

    def delete(self, path: str, bucket: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        fs.delete(p, recursive=True)
        return True, ""

    def exists(self, path: str, bucket: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        if fs.exists(p):
            if fs.isfile(p):
                return True, ""
            else:
                return False, f"Not File."
        else:
            return False, f"Not Exists {str(p)}"

    def absent(self, path: str, bucket: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        if fs.exists(p):
            return False, f"Exists {str(p)}"
        else:
            return True, ""


class FsspecDirOperator(FsspecRootOperator):
    def create(self, path: str, bucket: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        if not fs.exists(p):
            fs.mkdirs(p, exist_ok=True)
        return True, ""

    def delete(self, path: str, bucket: str = "", *args, **kwargs):
        if not path:
            raise RuntimeError()

        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        fs.rmdir(p)
        return True, ""

    def exists(self, path: str, bucket: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        if fs.exists(p):
            if fs.isdir(p):
                return True, ""
            else:
                return False, f"Not directory."
        else:
            return False, f"Not Exists {str(p)}"

    def absent(self, path: str, bucket: str = "", *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket, path)
        if fs.exists(p):
            return False, f"Exists {str(p)}"
        else:
            return True, ""


class FsspecBucketOperator(FsspecRootOperator):
    def create(self, bucket: str, *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket)
        fs.mkdir(p)
        if not fs.exists(p):
            fs.mkdirs(p, exist_ok=True)
        return True, ""

    def delete(self, bucket: str, *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket)
        fs.rmdir(p)
        return True, ""

    def exists(self, bucket: str, *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket)
        if fs.exists(p):
            if fs.isdir(p):
                return True, ""
            else:
                return False, f"Not directory."
        else:
            return False, f"Not Exists {str(p)}"

    def absent(self, bucket: str, *args, **kwargs):
        fs = self.get_filesystem()
        p = safe_join(bucket)
        if fs.exists(p):
            return False, f"Exists {str(p)}"
        else:
            return True, ""
