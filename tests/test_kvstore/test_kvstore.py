from rctl2.kvstores import serializers
import fsspec
from fsspec.core import url_to_fs

from rctl2.kvstores.stores import FileStore


def test_kvstore():

    print(fsspec.available_protocols())

    serializer = serializers.JsonSerializer()
    fs, path = url_to_fs("dir::file://test_kvstore")
    handler = FileStore(fs, serializer)

    print(f"############# {path}")
    for k in handler.keys():
        print(k)

    # print(handler.get("fsspec/local/test.txt"))

    print(handler.to_dict())

    # for k, v in handler.items(""):
    #     print((k, v))
