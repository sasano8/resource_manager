import hvac
import pytest

from rctl2.filesystems import VaultFileSystem
from rctl2.resources.dockercompose import DockerComposeSericeManager

RCTL2TEST_VALUT_URL = "http://127.0.0.1:8200"
RCTL2TEST_VALUT_TOKEN = "vaulttoken"
RCTL2TEST_VALUT_MOUNTPOINT = "secret"
RCTL2TEST_VALUT_DOCKER = "vault"  # dockercompose.yml 内の Vaultのサービス名
COUNTER = 0

VaultInstanceManager = DockerComposeSericeManager(service_name=RCTL2TEST_VALUT_DOCKER)


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
