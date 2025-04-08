import json
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO, StringIO
from unittest.mock import MagicMock, patch

import hvac
import pytest

from rctl2.filesystems import VaultFileSystem

from .conftest import VaultInstanceManager


@contextmanager
def skip_if_raises(reason, *exceptions):
    try:
        yield
    except exceptions as e:
        content = f"{str(e.__class__)}, {str(e)}, {reason}"
        pytest.skip(reason=content)


def test_is_authenticated_false(vault_fs: VaultFileSystem):
    if VaultInstanceManager.exists():
        pytest.skip("Vault インスタンスは起動中のためスキップ")

    assert not vault_fs.is_authenticated()
    with pytest.raises(Exception):
        vault_fs._authenticate()


def test_is_authenticated_true(vault_fs: VaultFileSystem):
    # Vault サービスを起動する
    if not VaultInstanceManager.exists():
        print("\n### Starting Vault Instance.")
        VaultInstanceManager.up(sleep=1)

    assert vault_fs.is_authenticated()
    assert vault_fs._authenticate()


def test_client(client: hvac.Client, params):
    assert client.is_authenticated()

    mount_point, path, secret = params
    secret = {"username": "test", "password": "test"}

    # 登録できること
    # 中身は作成情報だけ。登録した値は載っかってこない。
    result = client.secrets.kv.v2.create_or_update_secret(
        mount_point=mount_point, path=path, secret=secret
    )
    assert result

    # メタデータを取得できること
    metadata = client.secrets.kv.v2.read_secret_metadata(
        mount_point=mount_point, path=path
    )

    # 作成時のメタデータとは一致しない
    assert metadata
    assert result != metadata

    # 何度も登録できること
    result = client.secrets.kv.v2.create_or_update_secret(
        mount_point=mount_point, path=path, secret=secret
    )
    assert result

    # vault に登録できる値は辞書だけ
    with pytest.raises(hvac.exceptions.InvalidRequest, match="expected a map"):
        result = client.secrets.kv.v2.create_or_update_secret(
            mount_point=mount_point, path=path, secret="test"
        )

    # 登録した値が返ること
    result = client.secrets.kv.v2.read_secret_version(
        mount_point=mount_point,
        path=path,
        raise_on_deleted_version=True,
    )
    assert result["data"]["data"] == secret

    # 削除できること
    # 削除系の操作は２種類ある
    # destroy_secret_versions（ソフトデリート）
    # delete_metadata_and_all_versions（ハードデリート）
    res = client.secrets.kv.v2.delete_metadata_and_all_versions(
        path=path, mount_point=mount_point
    )
    assert res.status_code == 204  # no content

    # 何度削除しても同じ結果なこと
    res = client.secrets.kv.v2.delete_metadata_and_all_versions(
        path=path, mount_point=mount_point
    )
    assert res.status_code == 204  # no content

    # 何度削除しても同じ結果なこと
    res = client.secrets.kv.v2.destroy_secret_versions(
        path=path, mount_point=mount_point, versions=[1, 2, 3, 4, 5]
    )
    assert res.status_code == 204  # no content


def test_init(client: hvac.Client, params):
    """初期化のテスト"""
    mount_point, path, secret = params

    fs = VaultFileSystem.from_client(mount_point=mount_point, client=client)
    assert fs.protocol == "vault"
    assert fs.mount_point == mount_point

    fs = VaultFileSystem.from_url(
        mount_point=mount_point, url=client.url, token=client.token
    )
    assert fs.mount_point == mount_point


def test_normalize_path(vault_fs: VaultFileSystem):
    """パス正規化のテスト"""
    assert vault_fs._normalize_path("/test/path/") == "test/path"
    assert vault_fs._normalize_path("test/path") == "test/path"
    assert vault_fs._normalize_path("//test//path//") == "test/path"


def test_read_secret(vault_fs: VaultFileSystem, params):
    mount_point, path, secret = params
    """シークレット読み取りのテスト"""
    response = vault_fs._read_secret(path)
    assert response["data"]["data"] == secret


def test_read_secret_not_found(vault_fs: VaultFileSystem):
    """存在しないシークレットの読み取りテスト"""
    with pytest.raises(FileNotFoundError):
        vault_fs._read_secret("not_exists_key")


def test_write_secret_json(vault_fs: VaultFileSystem, params):
    """JSONシークレット書き込みのテスト"""
    mount_point, path, secret = params

    secret = {"value": "1"}
    json_content = json.dumps(secret)
    res = vault_fs._write_secret(path, json_content)
    assert res is None

    res = vault_fs._read_secret(path)
    assert res["data"]["data"] == secret


def test_ls_detail_false(vault_fs: VaultFileSystem, client: hvac.Client, mount_point):
    """ディレクトリリストのテスト"""

    # 空の状態を前提とする
    assert list(vault_fs.ls("", detail=False)) == []

    secret = {"value": "dummy"}
    json_content = json.dumps(secret)
    vault_fs._write_secret("key1", json_content)
    vault_fs._write_secret("key2", json_content)
    vault_fs._write_secret("key3/key4", json_content)

    assert set(vault_fs.ls("", detail=False)) == set(["key1", "key2", "key3/"])
    assert set(vault_fs.ls("key3", detail=False)) == set(["key4"])
    assert set(vault_fs.find("", detail=False, withdirs=False)) == set(
        ["key1", "key2", "key3/key4"]
    )
    assert set(vault_fs.find("key3", detail=False, withdirs=False)) == set(
        ["key3/key4"]
    )


def test_info(vault_fs: VaultFileSystem, params):
    """ファイル情報取得のテスト"""
    mount_point, path, secret = params
    info = vault_fs.info(path)
    assert info["name"] == path
    assert info["size"] is None
    assert info["type"] == "file"
    assert datetime.fromisoformat(info["created"])
    assert datetime.fromisoformat(info["modified"])


def test_exists(vault_fs: VaultFileSystem):
    """ファイル存在確認のテスト"""
    path = "not_exists_key"
    secret = {"value": "1"}
    json_content = json.dumps(secret)

    assert vault_fs.exists("not_exists_key") is False
    vault_fs._write_secret(path, json_content)
    assert vault_fs.exists("not_exists_key") is True


def test_open_read_text(vault_fs: VaultFileSystem, params):
    """テキスト読み取りモードのテスト"""
    mount_point, path, secret = params

    with vault_fs.open(path, mode="r") as f:
        content = json.load(f)
        assert isinstance(f, StringIO)
        assert content == secret


def test_open_read_binary(vault_fs: VaultFileSystem, params):
    """バイナリ読み取りモードのテスト"""
    mount_point, path, secret = params

    with vault_fs.open(path, mode="rb") as f:
        content = json.load(f)
        assert isinstance(f, BytesIO)
        assert content == secret


def test_open_write(vault_fs: VaultFileSystem, params):
    """書き込みモードのテスト"""
    mount_point, path, secret = params

    # テキストモードの検証
    value = {"value": "test_w"}

    with vault_fs.open(path, mode="w") as f:
        f.write(json.dumps(value))

    with vault_fs.open(path, mode="r") as f:
        assert json.load(f) == value

    # バイナリモードの検証
    value = {"value": "test_wb"}

    with vault_fs.open(path, mode="wb") as f:
        f.write(json.dumps(value))

    with vault_fs.open(path, mode="rb") as f:
        assert json.load(f) == value

    # 未サポートのモードの検証
    with pytest.raises(ValueError):
        vault_fs.open(path, mode="a")

    with skip_if_raises(
        "サポートするモード/しないモードを洗い出しきちんとテストすること", ValueError
    ):
        vault_fs.open(path, mode="a")


def test_rm(vault_fs: VaultFileSystem, params):
    """ファイル削除のテスト"""
    mount_point, path, secret = params

    assert vault_fs.exists(path)

    # 指定したパスが削除されること
    result = vault_fs.rm(path, recursive=False)
    assert result is None
    assert not vault_fs.exists(path)

    # 何度実行しても同じ結果が得られること
    result = vault_fs.rm(path, recursive=False)
    assert result is None
    assert not vault_fs.exists(path)

    # 再帰的な削除がサポートされていること
    with skip_if_raises("recursive=Trueは未サポート", NotImplementedError):
        result = vault_fs.rm(path, recursive=True)
