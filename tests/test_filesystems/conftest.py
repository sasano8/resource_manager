import json
import pytest
from unittest.mock import MagicMock

from rctl2.filesystems import VaultFileSystem

RCTL2TEST_VALUT_URL = "http://127.0.0.1:8200"
RCTL2TEST_VALUT_TOKEN = "vaulttoken"
RCTL2TEST_VALUT_MOUNTPOINT = "secret"
COUNTER = 0


def _vault_client():
    import hvac

    client = hvac.Client(url=RCTL2TEST_VALUT_URL, token=RCTL2TEST_VALUT_TOKEN)
    mount_point = RCTL2TEST_VALUT_MOUNTPOINT
    return client, mount_point


@pytest.fixture(scope="session")
def client():
    client, mount_point = _vault_client()
    return client


@pytest.fixture
def params():
    global COUNTER
    COUNTER += 1
    path = f"test/secret{COUNTER}"

    # vault に登録できる値は辞書のみ
    secret = {"username": f"user{COUNTER}", "password": f"pass{COUNTER}"}
    client, mount_point = _vault_client()

    assert client.secrets.kv.v2.create_or_update_secret(
        mount_point=mount_point, path=path, secret=secret
    )

    yield mount_point, path, secret

    res = client.secrets.kv.v2.delete_metadata_and_all_versions(
        path=path, mount_point=mount_point
    )
    assert res.status_code == 204  # no content


@pytest.fixture
def vault_fs():
    """VaultFileSystemのインスタンスを提供するフィクスチャ（モック使用）"""
    client, mount_point = _vault_client()
    fs = VaultFileSystem.from_client(client=client, mount_point=mount_point)

    # モックの設定
    mock_client = MagicMock()
    fs.client = mock_client

    # テスト用のパスとコンテンツ
    fs.test_path = "test/secret"
    fs.test_content = {"username": "testuser", "password": "testpass"}

    # テスト用のレスポンス
    fs.mock_read_response = {
        "data": {
            "data": {"value": json.dumps(fs.test_content)},
            "metadata": {"created_time": "2023-01-01T00:00:00Z", "version": 1},
        }
    }

    fs.mock_list_response = {"data": {"keys": ["secret1", "secret2"]}}

    fs.mock_metadata_response = {
        "data": {
            "created_time": "2023-01-01T00:00:00Z",
            "current_version": 1,
            "oldest_version": 1,
            "updated_time": "2023-01-01T00:00:00Z",
            "versions": {"1": {"created_time": "2023-01-01T00:00:00Z"}},
        }
    }

    # モックの戻り値を設定
    mock_client.secrets.kv.v2.read_secret_version.return_value = fs.mock_read_response
    mock_client.secrets.kv.v2.list_secrets.return_value = fs.mock_list_response
    mock_client.secrets.kv.v2.read_secret_metadata.return_value = (
        fs.mock_metadata_response
    )

    return fs


@pytest.fixture(scope="session")
def vault_test_data():
    """テスト用のデータをVaultに登録し、テスト後に削除するフィクスチャ"""
    client, mount_point = _vault_client()

    test_paths = ["test/secret1", "test/secret2", "test/nested/secret3"]
    test_contents = [
        {"username": "user1", "password": "pass1"},
        {"username": "user2", "password": "pass2"},
    ]

    # テストデータを登録
    for path, content in zip(test_paths, test_contents):
        if isinstance(content, dict):
            # JSONデータの場合
            client.secrets.kv.v2.create_or_update_secret(
                path=path, secret=content, mount_point=mount_point
            )
        else:
            raise Exception("Valut はキーバリューペアしか受け付けません")

    # テストデータのパスと内容を返す
    test_data = {
        "paths": test_paths,
        "contents": test_contents,
        "mount_point": mount_point,
    }

    yield test_data

    # テスト後にデータを削除
    # for path in test_paths:
    #     try:
    #         vault_client.secrets.kv.v2.delete_metadata_and_all_versions(
    #             path=path, mount_point=mount_point
    #         )
    #     except Exception:
    #         # 削除に失敗してもテストは続行
    #         pass


@pytest.fixture
def real_vault_fs(vault_test_data):
    """実際のVaultサーバーに接続するVaultFileSystemのインスタンスを提供するフィクスチャ"""
    client, mount_point = _vault_client()
    mount_point = vault_test_data["mount_point"]

    fs = VaultFileSystem.from_client(mount_point=mount_point, client=client)

    # テストデータのパスと内容を追加
    fs.test_paths = vault_test_data["paths"]
    fs.test_contents = vault_test_data["contents"]

    return fs
