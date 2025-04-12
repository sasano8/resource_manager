from os import environ

import pytest

from rctl2.filesystems import EnvFileSystem


@pytest.mark.parametrize("cache", [True, False])
def test_init(cache):
    assert EnvFileSystem(cache=cache)


@pytest.mark.parametrize("cache", [True, False])
def test_exists(cache):
    fs = EnvFileSystem(cache=cache)
    assert fs.exists("HOME")
    assert not fs.exists("NOT EXISTS KEY")


@pytest.mark.parametrize("cache", [True, False])
def test_info(cache):
    fs = EnvFileSystem(cache=cache)
    info = fs.info("HOME")
    assert info == {"name": "HOME", "size": None, "type": "file"}


@pytest.mark.parametrize("cache", [True, False])
def test_ls_detail_false(cache):
    fs = EnvFileSystem(cache=cache)
    assert fs.ls("", detail=False) == list(environ.keys())


@pytest.mark.parametrize("cache", [True, False])
def test_ls_detail_true(cache):
    fs = EnvFileSystem(cache=cache)
    assert [x["name"] for x in fs.ls("", detail=True)] == list(environ.keys())
    for x in fs.ls("", detail=True):
        assert x["size"] is None
        assert x["type"] == "file"


@pytest.mark.parametrize("cache", [True, False])
def test_find_detail_false(cache):
    fs = EnvFileSystem(cache=cache)
    assert fs.find("", detail=False) == list(environ.keys())


@pytest.mark.parametrize("cache", [True, False])
def test_find_detail_true(cache):
    fs = EnvFileSystem(cache=cache)
    assert [x["name"] for x in fs.ls("", detail=True)] == list(environ.keys())
    for x in fs.find("", detail=True):
        assert x["size"] is None
        assert x["type"] == "file"


@pytest.mark.parametrize("cache", [True, False])
def test_open(cache):
    fs = EnvFileSystem(cache=cache)
    with fs.open("HOME", mode="r") as f:
        assert f.read() == environ["HOME"]

    with fs.open("HOME", mode="rb") as f:
        assert f.read() == environ["HOME"].encode("UTF8")
