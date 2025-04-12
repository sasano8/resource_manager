import fsspec

from rctl2.filesystems import ArrayFileSystem, VaultFileSystem

from .conftest import (
    RCTL2TEST_VALUT_MOUNTPOINT,
    RCTL2TEST_VALUT_TOKEN,
    RCTL2TEST_VALUT_URL,
)


def test_fsspec_filesystem():
    params = {
        "protocol": "vault",
        "url": RCTL2TEST_VALUT_URL,
        "token": RCTL2TEST_VALUT_TOKEN,
        "mount_point": RCTL2TEST_VALUT_MOUNTPOINT,
    }

    fs = fsspec.filesystem(**params)
    assert isinstance(fs, VaultFileSystem)


# def test_from_dict():
#     array = ArrayFileSystem.from_dict(
#         {
#             "store1": {
#                 "params": {
#                     "protocol": "vault",
#                     "url": RCTL2TEST_VALUT_URL,
#                     "token": RCTL2TEST_VALUT_TOKEN,
#                     "mount_point": "secret",
#                 }
#             }
#         }
#     )

#     assert len(array._filesystems) == 1
#     fs = array._filesystems["store1"]
#     assert isinstance(fs, VaultFileSystem)
