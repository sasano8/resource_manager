import os
import json
import pytest
from io import BytesIO, StringIO
from unittest.mock import MagicMock, patch

import hvac
import fsspec
from rctl2.filesystems import VaultFileSystem


# @pytest.fixture
# def vault_fs():
#     """VaultFileSystemのインスタンスを作成する"""
#     fs = VaultFileSystem(url="http://127.0.0.1:8200", token="vaulttoken")
#     fs.client = MagicMock()

#     # テスト用のパスとコンテンツ
#     test_path = "test/secret1"
#     test_content = {"value": "test content"}

#     # モックの設定
#     fs.client.secrets.kv.v2.read_secret_version.return_value = {
#         "data": {"data": test_content}
#     }
#     fs.client.secrets.kv.v2.list_secrets.return_value = {
#         "data": {"keys": ["secret1", "secret2", "nested/secret3"]}
#     }
#     fs.client.secrets.kv.v2.read_secret_metadata.return_value = {
#         "data": {"created_time": "2024-01-01T00:00:00Z"}
#     }

#     return fs


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
        mount_point=mount_point, path=path
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


def test_init(client: hvac.Client):
    """初期化のテスト"""
    mount_point = "secret"
    fs = VaultFileSystem(url=client.url, token=client.token, mount_point=mount_point)
    assert fs.protocol == "vault"
    assert fs.mount_point == mount_point


def test_normalize_path(vault_fs: VaultFileSystem):
    """パス正規化のテスト"""
    assert vault_fs._normalize_path("/test/path/") == "test/path"
    assert vault_fs._normalize_path("test/path") == "test/path"
    assert vault_fs._normalize_path("//test//path//") == "test/path"


def test_path_to_key(vault_fs: VaultFileSystem):
    """パスからキーへの変換テスト"""
    assert vault_fs._path_to_key("/test/path/") == "test/path"
    assert vault_fs._path_to_key("test/path") == "test/path"


def test_key_to_path(vault_fs: VaultFileSystem):
    """キーからパスへの変換テスト"""
    assert vault_fs._key_to_path("test/path") == "/test/path"


def test_read_secret(vault_fs: VaultFileSystem, params):
    mount_point, path, secret = params
    """シークレット読み取りのテスト"""
    response = vault_fs._read_secret(path)
    res = vault_fs.client.secrets.kv.v2.read_secret_version(
        path=path, mount_point=vault_fs.mount_point
    )
    assert res["data"]["data"]["value"] == secret


def test_read_secret_not_found(vault_fs: VaultFileSystem):
    """存在しないシークレットの読み取りテスト"""
    vault_fs.client.secrets.kv.v2.read_secret_version.side_effect = Exception(
        "InvalidPath"
    )
    with pytest.raises(FileNotFoundError):
        vault_fs._read_secret(vault_fs.test_path)


def test_write_secret_json(vault_fs: VaultFileSystem):
    """JSONシークレット書き込みのテスト"""
    json_content = json.dumps(vault_fs.test_content)
    vault_fs._write_secret(vault_fs.test_path, json_content)
    vault_fs.client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path=vault_fs.test_path,
        secret=vault_fs.test_content,
        mount_point=vault_fs.mount_point,
    )


def test_write_secret_string(vault_fs: VaultFileSystem):
    """文字列シークレット書き込みのテスト"""
    string_content = "plain text content"
    vault_fs._write_secret(vault_fs.test_path, string_content)
    vault_fs.client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path=vault_fs.test_path,
        secret={"value": string_content},
        mount_point=vault_fs.mount_point,
    )


def test_ls(vault_fs: VaultFileSystem):
    """ディレクトリリストのテスト"""
    result = vault_fs.ls("")
    vault_fs.client.secrets.kv.v2.list_secrets.assert_called_once_with(
        path="", mount_point=vault_fs.mount_point
    )
    assert len(result) == 2
    assert result[0]["name"] == "/secret1"
    assert result[1]["name"] == "/secret2"


def test_ls_detail_false(vault_fs: VaultFileSystem):
    """詳細なしディレクトリリストのテスト"""
    result = vault_fs.ls("", detail=False)
    assert result == ["/secret1", "/secret2"]


def test_info(vault_fs: VaultFileSystem):
    """ファイル情報取得のテスト"""
    info = vault_fs.info(vault_fs.test_path)
    vault_fs.client.secrets.kv.v2.read_secret_metadata.assert_called_once_with(
        path=vault_fs.test_path, mount_point=vault_fs.mount_point
    )
    assert info["name"] == f"/{vault_fs.test_path}"
    assert info["type"] == "file"
    assert info["created"] == "2023-01-01T00:00:00Z"


def test_exists(vault_fs: VaultFileSystem):
    """ファイル存在確認のテスト"""
    assert vault_fs.exists(vault_fs.test_path) is True
    vault_fs.client.secrets.kv.v2.read_secret_metadata.assert_called_once_with(
        path=vault_fs.test_path, mount_point=vault_fs.mount_point
    )


def test_exists_not_found(vault_fs: VaultFileSystem):
    """存在しないファイルの確認テスト"""
    vault_fs.client.secrets.kv.v2.read_secret_metadata.side_effect = Exception(
        "InvalidPath"
    )
    assert vault_fs.exists(vault_fs.test_path) is False


def test_cat(vault_fs: VaultFileSystem):
    """ファイル内容取得のテスト"""
    content = vault_fs.cat(vault_fs.test_path)
    vault_fs.client.secrets.kv.v2.read_secret_version.assert_called_once_with(
        path=vault_fs.test_path, mount_point=vault_fs.mount_point
    )
    assert content == json.dumps(vault_fs.test_content)


def test_open_read_text(vault_fs: VaultFileSystem):
    """テキスト読み取りモードのテスト"""
    with vault_fs.open(vault_fs.test_path, mode="r") as f:
        content = f.read()
        assert isinstance(f, StringIO)
        assert content == json.dumps(vault_fs.mock_read_response)


def test_open_read_binary(vault_fs: VaultFileSystem):
    """バイナリ読み取りモードのテスト"""
    with vault_fs.open(vault_fs.test_path, mode="rb") as f:
        content = f.read()
        assert isinstance(f, BytesIO)
        assert content == json.dumps(vault_fs.mock_read_response).encode()


def test_open_write(vault_fs: VaultFileSystem):
    """書き込みモードのテスト"""
    with vault_fs.open(vault_fs.test_path, mode="w") as f:
        f.write(json.dumps(vault_fs.test_content))
        # closeメソッドが呼ばれるまでVaultには書き込まれない
        vault_fs.client.secrets.kv.v2.create_or_update_secret.assert_not_called()

    # closeメソッドが呼ばれた後にVaultに書き込まれる
    vault_fs.client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path=vault_fs.test_path,
        secret=vault_fs.test_content,
        mount_point=vault_fs.mount_point,
    )


def test_open_unsupported_mode(vault_fs: VaultFileSystem):
    """サポートされていないモードのテスト"""
    with pytest.raises(ValueError):
        vault_fs.open(vault_fs.test_path, mode="a")


def test_rm(vault_fs: VaultFileSystem):
    """ファイル削除のテスト"""
    vault_fs.rm(vault_fs.test_path)
    vault_fs.client.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once_with(
        path=vault_fs.test_path, mount_point=vault_fs.mount_point
    )


def test_rm_not_found(vault_fs: VaultFileSystem):
    """存在しないファイルの削除テスト"""
    vault_fs.client.secrets.kv.v2.delete_metadata_and_all_versions.side_effect = (
        Exception("InvalidPath")
    )
    with pytest.raises(FileNotFoundError):
        vault_fs.rm(vault_fs.test_path)


# 実際のVaultサーバーを使用したテスト


def test_real_read_secret(vault_fs: VaultFileSystem, params):
    """実際のVaultサーバーを使用したシークレット読み取りのテスト"""
    mount_point, path, secret = params

    # 最初のテストデータを読み取る
    # path = real_vault_fs.test_paths[0]
    # content = real_vault_fs.test_contents[0]

    # シークレットを読み取る
    response = vault_fs._read_secret(path)

    # レスポンスを検証
    assert "data" in response
    assert "data" in response["data"]
    assert "value" in response["data"]["data"]

    # 値が正しく取得できているか確認
    read_value = json.loads(response["data"]["data"]["value"])
    assert read_value == secret


def test_real_write_secret(real_vault_fs):
    """実際のVaultサーバーを使用したシークレット書き込みのテスト"""
    # 新しいテストデータ
    path = "test/written_secret"
    content = {"new_key": "new_value"}

    # シークレットを書き込む
    real_vault_fs._write_secret(path, json.dumps(content))

    # 書き込んだシークレットを読み取る
    response = real_vault_fs._read_secret(path)
    read_value = json.loads(response["data"]["data"]["value"])

    # 値が正しく書き込まれているか確認
    assert read_value == content

    # テスト後に削除
    real_vault_fs.rm(path)


def test_real_ls(real_vault_fs):
    """実際のVaultサーバーを使用したディレクトリリストのテスト"""
    # ルートディレクトリのリストを取得
    result = real_vault_fs.ls("")

    # 結果を検証
    assert isinstance(result, list)
    assert len(result) > 0

    # テストデータのパスが含まれているか確認
    test_paths = [f"/{path}" for path in real_vault_fs.test_paths]
    for path in test_paths:
        assert any(item["name"] == path for item in result)


def test_real_exists(real_vault_fs):
    """実際のVaultサーバーを使用したファイル存在確認のテスト"""
    # 存在するファイル
    assert real_vault_fs.exists(real_vault_fs.test_paths[0]) is True

    # 存在しないファイル
    assert real_vault_fs.exists("non_existent_path") is False


def test_real_cat(real_vault_fs):
    """実際のVaultサーバーを使用したファイル内容取得のテスト"""
    # 最初のテストデータを読み取る
    path = real_vault_fs.test_paths[0]
    content = real_vault_fs.test_contents[0]

    # ファイル内容を取得
    result = real_vault_fs.cat(path)

    # 結果を検証
    assert isinstance(result, str)
    read_value = json.loads(result)
    assert read_value == content


def test_real_open_read(real_vault_fs):
    """実際のVaultサーバーを使用したファイル読み取りのテスト"""
    # 最初のテストデータを読み取る
    path = real_vault_fs.test_paths[0]
    content = real_vault_fs.test_contents[0]

    # ファイルを開いて読み取る
    with real_vault_fs.open(path, mode="r") as f:
        result = f.read()

    # 結果を検証
    assert isinstance(result, str)
    read_value = json.loads(result)
    assert read_value == content


def test_real_open_write(real_vault_fs):
    """実際のVaultサーバーを使用したファイル書き込みのテスト"""
    # 新しいテストデータ
    path = "test/written_file"
    content = {"file_key": "file_value"}

    # ファイルを開いて書き込む
    with real_vault_fs.open(path, mode="w") as f:
        f.write(json.dumps(content))

    # 書き込んだファイルを読み取る
    with real_vault_fs.open(path, mode="r") as f:
        result = f.read()

    # 結果を検証
    read_value = json.loads(result)
    assert read_value == content

    # テスト後に削除
    real_vault_fs.rm(path)


def test_is_authenticated_success(vault_fs: VaultFileSystem):
    """is_authenticated()が成功する場合のテスト"""
    vault_fs.client.is_authenticated.return_value = True
    assert vault_fs.is_authenticated() is True


def test_is_authenticated_failure(vault_fs: VaultFileSystem):
    """is_authenticated()が失敗する場合のテスト"""
    vault_fs.client.is_authenticated.return_value = False
    assert vault_fs.is_authenticated() is False


def test_is_authenticated_exception(vault_fs: VaultFileSystem):
    """is_authenticated()で例外が発生する場合のテスト"""
    vault_fs.client.is_authenticated.side_effect = Exception("Connection error")
    assert vault_fs.is_authenticated() is False


def test_connect_success():
    """_connect()が成功する場合のテスト"""
    with patch("rctl2.filesystems.VaultFileSystem.is_authenticated", return_value=True):
        fs = VaultFileSystem(url="http://127.0.0.1:8200", token="vaulttoken")
        # 例外が発生しなければ成功


def test_connect_failure():
    """_connect()が失敗する場合のテスト"""
    with patch(
        "rctl2.filesystems.VaultFileSystem.is_authenticated", return_value=False
    ):
        with pytest.raises(ConnectionError) as exc_info:
            VaultFileSystem(url="http://127.0.0.1:8200", token="vaulttoken")
        assert "Vaultサーバーに接続できません" in str(exc_info.value)


def test_init_with_client():
    """クライアントでの初期化テスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    fs = VaultFileSystem(client=mock_client)
    assert fs.client == mock_client
    assert fs.mount_point == "secret"


def test_init_with_client_and_mount_point():
    """クライアントとマウントポイントでの初期化テスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    fs = VaultFileSystem(client=mock_client, mount_point="custom")
    assert fs.client == mock_client
    assert fs.mount_point == "custom"


def test_init_with_client_and_url():
    """クライアントとURLでの初期化テスト（エラーになるべき）"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem(client=mock_client, url="http://127.0.0.1:8200")
    assert (
        "When providing a client, url and token parameters should not be provided"
        in str(exc_info.value)
    )


def test_init_with_client_and_token():
    """クライアントとトークンでの初期化テスト（エラーになるべき）"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem(client=mock_client, token="vaulttoken")
    assert (
        "When providing a client, url and token parameters should not be provided"
        in str(exc_info.value)
    )


def test_init_without_params():
    """パラメータなしでの初期化テスト"""
    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem()
    assert "Either client or both url and token must be provided" in str(exc_info.value)


def test_from_client():
    """from_clientファクトリーメソッドのテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    fs = VaultFileSystem.from_client(mock_client)
    assert fs.client == mock_client
    assert fs.mount_point == "secret"


def test_from_client_with_mount_point():
    """from_clientファクトリーメソッドでマウントポイントを指定するテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    fs = VaultFileSystem.from_client(mock_client, mount_point="custom")
    assert fs.client == mock_client
    assert fs.mount_point == "custom"


def test_from_url():
    """from_urlファクトリーメソッドのテスト"""
    with patch("hvac.Client") as mock_client:
        mock_client.return_value = MagicMock()
        mock_client.return_value.is_authenticated.return_value = True

        fs = VaultFileSystem.from_url(
            "http://127.0.0.1:8200", "vaulttoken", mount_point="custom"
        )
        assert fs.client == mock_client.return_value
        assert fs.mount_point == "custom"
        assert fs.client.mount_point == "custom"


def test_init_with_client_and_url_and_token():
    """クライアント、URL、トークンが同時に指定された場合のテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem(
            client=mock_client, url="http://127.0.0.1:8200", token="vaulttoken"
        )
    assert (
        "When providing a client, url and token parameters should not be provided"
        in str(exc_info.value)
    )


def test_init_with_client_and_mount_point_and_url():
    """クライアント、マウントポイント、URLが同時に指定された場合のテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem(
            client=mock_client, mount_point="custom", url="http://127.0.0.1:8200"
        )
    assert (
        "When providing a client, url and token parameters should not be provided"
        in str(exc_info.value)
    )


def test_init_with_client_and_mount_point_and_token():
    """クライアント、マウントポイント、トークンが同時に指定された場合のテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem(client=mock_client, mount_point="custom", token="vaulttoken")
    assert (
        "When providing a client, url and token parameters should not be provided"
        in str(exc_info.value)
    )


def test_init_with_client_and_mount_point_and_url_and_token():
    """クライアント、マウントポイント、URL、トークンが同時に指定された場合のテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    with pytest.raises(ValueError) as exc_info:
        VaultFileSystem(
            client=mock_client,
            mount_point="custom",
            url="http://127.0.0.1:8200",
            token="vaulttoken",
        )
    assert (
        "When providing a client, url and token parameters should not be provided"
        in str(exc_info.value)
    )


def test_init_with_hvac_args():
    """hvac.Clientの引数を使用した初期化テスト"""
    with patch("hvac.Client") as mock_client:
        mock_client.return_value = MagicMock()
        mock_client.return_value.is_authenticated.return_value = True

        fs = VaultFileSystem(
            url="http://127.0.0.1:8200",
            token="vaulttoken",
            cert=("cert.pem", "key.pem"),
            verify=False,
            timeout=60,
            proxies={"http": "http://proxy:8080"},
            allow_redirects=False,
            namespace="admin",
        )

        # hvac.Clientが正しい引数で初期化されたことを確認
        mock_client.assert_called_once_with(
            url="http://127.0.0.1:8200",
            token="vaulttoken",
            cert=("cert.pem", "key.pem"),
            verify=False,
            timeout=60,
            proxies={"http": "http://proxy:8080"},
            allow_redirects=False,
            namespace="admin",
        )

        assert fs.client == mock_client.return_value
        assert fs.mount_point == "secret"


def test_from_url_with_hvac_args():
    """hvac.Clientの引数を使用したfrom_urlテスト"""
    with patch("hvac.Client") as mock_client:
        mock_client.return_value = MagicMock()
        mock_client.return_value.is_authenticated.return_value = True

        fs = VaultFileSystem.from_url(
            url="http://127.0.0.1:8200",
            token="vaulttoken",
            cert=("cert.pem", "key.pem"),
            verify=False,
            timeout=60,
            proxies={"http": "http://proxy:8080"},
            allow_redirects=False,
            namespace="admin",
        )

        # hvac.Clientが正しい引数で初期化されたことを確認
        mock_client.assert_called_once_with(
            url="http://127.0.0.1:8200",
            token="vaulttoken",
            cert=("cert.pem", "key.pem"),
            verify=False,
            timeout=60,
            proxies={"http": "http://proxy:8080"},
            allow_redirects=False,
            namespace="admin",
        )

        assert fs.client == mock_client.return_value
        assert fs.mount_point == "secret"


def test_write_with_string_data():
    """文字列データを直接渡した場合のテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    fs = VaultFileSystem(client=mock_client)

    # 文字列データを渡す
    content = "test data"

    # 文字列データは自動的に {"value": content} に変換される
    fs.write("test/path", content)

    # hvac.Clientのメソッドが正しく呼び出されたことを確認
    mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path="test/path", secret={"value": content}, mount_point="secret"
    )


def test_write_with_json_data():
    """JSONデータを渡した場合のテスト"""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    fs = VaultFileSystem(client=mock_client)

    # JSONデータを渡す
    content = json.dumps({"key": "value"})

    # JSONデータはそのまま使用される
    fs.write("test/path", content)

    # hvac.Clientのメソッドが正しく呼び出されたことを確認
    mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path="test/path", secret={"key": "value"}, mount_point="secret"
    )
