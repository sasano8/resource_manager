import hvac
import pytest

from rctl2.filesystems import VaultFileSystem

RCTL2TEST_VALUT_URL = "http://127.0.0.1:8200"
RCTL2TEST_VALUT_TOKEN = "vaulttoken"
RCTL2TEST_VALUT_MOUNTPOINT = "secret"
COUNTER = 0


class DockerComposeSericeManager:
    def __init__(self, service_name):
        self._service_name = service_name

    def exists(self):
        import os
        import subprocess

        result = subprocess.run(
            ["docker", "compose", "ps", self._service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )

        if result.returncode:
            return False

        # docker compose にサービスが定義されていると、常に returncode == 0 が返る
        # Up されているか確認する
        for line in result.stdout.splitlines():
            if self._service_name in line and "Up" in line:
                return True

        return False

    def up(self, sleep: int = 1):
        if not self.exists():
            import subprocess
            import time

            subprocess.run(["docker", "compose", "up", "-d", self._service_name])
            time.sleep(sleep)

    def down(self):
        import subprocess

        subprocess.run(["docker", "compose", "down", self._service_name])


VaultInstanceManager = DockerComposeSericeManager("vault")


def _vault_client():
    client = hvac.Client(url=RCTL2TEST_VALUT_URL, token=RCTL2TEST_VALUT_TOKEN)
    mount_point = RCTL2TEST_VALUT_MOUNTPOINT
    return mount_point, client


@pytest.fixture(scope="session")
def client():
    mount_point, client = _vault_client()
    return client


@pytest.fixture
def mount_point():
    return RCTL2TEST_VALUT_MOUNTPOINT


@pytest.fixture(scope="session")
def vault_fs():
    mount_point, client = _vault_client()
    fs = VaultFileSystem.from_client(mount_point=mount_point, client=client)
    return fs


@pytest.fixture(autouse=True)
def cleanup():
    if not VaultInstanceManager.exists():
        yield None, None
        return

    mount_point, client = _vault_client()
    fs = VaultFileSystem.from_client(mount_point=mount_point, client=client)

    for path in fs.find("", withdirs=False):
        client.secrets.kv.v2.delete_metadata_and_all_versions(
            mount_point=mount_point, path=path
        )

    yield mount_point, client


@pytest.fixture
def params(cleanup):
    global COUNTER
    COUNTER += 1

    mount_point, client = cleanup
    path = f"test/secret{COUNTER}"

    # vault に登録できる値は辞書のみ
    secret = {"username": f"user{COUNTER}", "password": f"pass{COUNTER}"}

    assert client.secrets.kv.v2.create_or_update_secret(
        mount_point=mount_point, path=path, secret=secret
    )

    yield mount_point, path, secret

    res = client.secrets.kv.v2.delete_metadata_and_all_versions(
        path=path, mount_point=mount_point
    )
    assert res.status_code == 204  # no content
