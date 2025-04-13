import json
import os

from rctl2 import filesystems

from .conftest import (
    RCTL2TEST_VALUT_MOUNTPOINT,
    RCTL2TEST_VALUT_TOKEN,
    RCTL2TEST_VALUT_URL,
)


def loads_json(s, extension=""):
    return json.loads(s)


def test_extract_ext():
    from rctl2.filesystems.utils import extract_ext

    assert extract_ext("file.json") == "json"
    assert extract_ext("file.old.json") == "json"
    assert extract_ext("a/file.old.json") == "json"
    assert extract_ext("text") == ""
    assert extract_ext("a/text") == ""
    assert extract_ext("text.") == ""
    assert extract_ext("a/text.") == ""
    assert extract_ext(".txt") == ""
    assert extract_ext("a/.txt") == ""


def test_normalize_path():
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


# @pytest.mark.xfail(reason="未実装")
def test_get_store_local():
    store = filesystems.get_store(
        "local", storage_options={}, root="tests/data/json_store", loader=loads_json
    )

    assert store == {
        "a.json": {"b": "1", "c": {"d": "2"}},
        "b/c.json": {"e": "3", "f": {"g": "4"}},
    }

    store = filesystems.get_store(
        "local", storage_options={}, root="tests/data/json_store/b", loader=loads_json
    )

    assert store == {
        "c.json": {"e": "3", "f": {"g": "4"}},
    }


def test_get_store_env():
    store = filesystems.get_store("env", storage_options={}, root="", loader=loads_json)
    assert "RCTL_TEST_ENV1" not in store
    assert "RCTL_TEST_ENV2" not in store

    os.environ["RCTL_TEST_ENV1"] = "1"

    store = filesystems.get_store("env", storage_options={}, root="", loader=loads_json)

    assert "RCTL_TEST_ENV1" in store
    assert "RCTL_TEST_ENV2" not in store
    store["RCTL_TEST_ENV1"] == "1"

    os.environ["RCTL_TEST_ENV2"] = "2"

    store = filesystems.get_store("env", storage_options={}, root="", loader=loads_json)

    assert "RCTL_TEST_ENV1" in store
    assert "RCTL_TEST_ENV2" in store
    store["RCTL_TEST_ENV1"] == "1"
    store["RCTL_TEST_ENV2"] == "2"


def test_get_store_vault(vault_fs: filesystems.VaultFileSystem):
    assert vault_fs.find("") == []
    with vault_fs.open("mysecret1", "w") as f:
        json.dump({"a": 1}, f)

    with vault_fs.open("group1/secret1", "w") as f:
        json.dump({"b": 2}, f)

    storage_options = {
        "url": RCTL2TEST_VALUT_URL,
        "token": RCTL2TEST_VALUT_TOKEN,
        "mount_point": RCTL2TEST_VALUT_MOUNTPOINT,
    }

    store = filesystems.get_store(
        "vault",
        storage_options=storage_options,
        root="",
        loader=loads_json,
    )

    assert set(vault_fs.find("", detail=False)) == set(["mysecret1", "group1/secret1"])
    assert store == {"mysecret1": {"a": 1}, "group1/secret1": {"b": 2}}

    store = filesystems.get_store(
        "vault",
        storage_options=storage_options,
        loader=loads_json,
        root="group1",
    )
    assert store == {"secret1": {"b": 2}}


def test_get_store_from_dict():
    data = {
        "protocol": "local",
        "storage_options": {},
        "loader": {"*": {"type": "json", "params": {}}},
        "root": "tests/data/json_store",
    }
    store = filesystems.get_store_from_dict(**data)
    assert store == {
        "a.json": {"b": "1", "c": {"d": "2"}},
        "b/c.json": {"e": "3", "f": {"g": "4"}},
    }


def test_get_stores_from_dict():
    data = {
        "store1": {
            "protocol": "local",
            "storage_options": {},
            "loader": {"*": {"type": "json", "params": {}}},
            "root": "tests/data/json_store",
        },
        "store2": {
            "protocol": "local",
            "storage_options": {},
            "loader": {"*": {"type": "json", "params": {}}},
            "root": "tests/data/json_store",
        },
    }

    stores = filesystems.get_stores_from_dict(**data)
    assert stores["store1"] == {
        "a.json": {"b": "1", "c": {"d": "2"}},
        "b/c.json": {"e": "3", "f": {"g": "4"}},
    }
    assert stores["store2"] == {
        "a.json": {"b": "1", "c": {"d": "2"}},
        "b/c.json": {"e": "3", "f": {"g": "4"}},
    }
