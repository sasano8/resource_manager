import json

import pytest

from rctl2 import filesystems

from .conftest import _vault_client


def test_normalize():
    from rctl2.filesystems.utils import normalize_path

    assert normalize_path("a") == "a"
    assert normalize_path("/") == ""
    assert normalize_path("/a") == "a"
    assert normalize_path("a/") == "a"
    assert normalize_path("/a/") == "a"
    assert normalize_path("") == ""
    assert normalize_path(".") == ""
    assert normalize_path("data.json") == "data.json"
    assert normalize_path("data.") == "data."
    assert normalize_path(".data") == ".data"
    assert normalize_path(".data.") == ".data."

    assert normalize_path("/a//b///c////d/////") == "a/b/c/d"
    assert normalize_path("./a//.///b////.") == "a/b"


@pytest.mark.xfail(reason="未実装")
def test_get_store_local():
    raise Exception(
        filesystems.get_store(
            "local", storage_options={}, root="test_kvstore", loader=json.loads
        )
    )


@pytest.mark.xfail(reason="未実装")
def test_get_store_env():
    store = filesystems.get_store("env", storage_options={}, root="", loader=json.loads)

    # for k, v in store.items():
    #     print(f"{k}={v}")

    raise NotImplementedError()


def test_get_store_vault(vault_fs: filesystems.VaultFileSystem):
    assert vault_fs.find("") == []
    with vault_fs.open("mysecret1", "w") as f:
        json.dump({"a": 1}, f)

    with vault_fs.open("group1/secret1", "w") as f:
        json.dump({"b": 2}, f)

    store = filesystems.get_store(
        "vault",
        storage_options={
            "url": "http://127.0.0.1:8200",
            "token": "vaulttoken",
            "mount_point": "secret",
        },
        root="",
        loader=json.loads,
    )

    assert store == {"mysecret1": {"a": 1}, "group1/secret1": {"b": 2}}
