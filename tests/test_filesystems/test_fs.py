import hvac
import pytest

from rctl2.filesystems import VaultFileSystem


def test_init():
    """クライアントでの初期化テスト"""

    client = hvac.Client("")

    # 一般的な初期化
    fs = VaultFileSystem(mount_point="secret", client=client)
    assert fs.client == client
    assert fs.mount_point == "secret"

    # マウントポイントは必須
    with pytest.raises(Exception) as exc_info:
        fs = VaultFileSystem(client=client)

    # client, url は一緒に指定できない
    with pytest.raises(ValueError, match="provided") as exc_info:
        VaultFileSystem(
            mount_point="secret", client=client, url="http://127.0.0.1:8200"
        )


def test_init_from_client():
    client = hvac.Client("")
    fs = VaultFileSystem.from_client(mount_point="secret", client=client)
    assert fs.client == client
    assert fs.mount_point == "secret"


def test_init_from_url():
    fs = VaultFileSystem.from_url(
        mount_point="secret", url="http://127.0.0.1:8200", token=""
    )
    assert fs.client
    assert fs.mount_point == "secret"
