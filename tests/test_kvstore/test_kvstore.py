from rctl2.kvstores import fsstore, serializers
import fsspec
from fsspec.core import url_to_fs


def test_kvstore():

    print(fsspec.available_protocols())

    serializer = serializers.TextSerializer()
    fs, path = url_to_fs("dir::file://test-cache")
    handler = fsstore.FileHandler(fs, serializer)

    print(f"############# {path}")
    for k in handler.keys():
        print(k)

    print(handler.get("fsspec/local/test.txt"))

    # for k, v in handler.items(""):
    #     print((k, v))
