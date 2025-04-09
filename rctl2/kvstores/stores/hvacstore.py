from io import FileIO, StringIO
from typing import Any, List, Optional

import hvac

from .abc import AbstractKVStore

# FileIO()


class VaultWriteIO:
    def __init__(self, client: "hvac.Client", initial_value: str = "", **kwargs):
        self._client = client
        self._buf = StringIO(initial_value)
        self._kwargs = kwargs

        a = StringIO(initial_value)
        a.write()
        a.read()
        a.flush()

    def write(self, s: str):
        return self._buf.write(s)

    def read(self, size: int = -1):
        return self._buf.read(size)

    def flush(self):
        self._buf.getvalue()
        self._client.secrets.kv.v2.create_or_update_secret(**self._kwargs)


class HashiCorpVaultStore(AbstractKVStore):
    def __init__(self, client: "hvac.Client", mount_point: str = "secret"):
        self.client = client
        self.mount_point = mount_point

    @classmethod
    def create(cls, mount_point: str = "secret", *, url: str, token: str, **kwargs):
        client = hvac.Client(url=url, token=token, **kwargs)
        return cls(client, mount_point)

    def open(self, *args, **kwargs):
        return self._fs.open(*args, **kwargs)

    def load(self, path):
        with self.open(path, "r") as f:
            return self._serializer.load(f)

    def dump(self, path):
        with self.open(path, "w") as f:
            return self._serializer.dump(f)

    def _wrap(self, key: str) -> str:
        # Vault ではパスで区切るのでスラッシュを安全に扱う
        return key.strip("/")

    def get(self, key: str, version: int | None = None) -> str | None:
        try:
            params = {"version": version} if version else {}
            response = self.client.secrets.kv.v2.read_secret_version(
                path=self._wrap(key),
                mount_point=self.mount_point,
                raise_on_deleted_version=True,
                **params,
            )
            return response["data"]["data"]["value"]
        except hvac.exceptions.InvalidPath:
            return None

    def set(self, key: str, value: str, ttl: int | None = None):
        # TTL は Vault 側では metadata やポリシーで管理（ここでは記録しない）
        self.client.secrets.kv.v2.create_or_update_secret(
            path=self._wrap(key), secret={"value": value}, mount_point=self.mount_point
        )

    def delete(self, key: str):
        self.client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=self._wrap(key), mount_point=self.mount_point
        )

    def list_keys(self) -> List[str]:
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path="", mount_point=self.mount_point
            )
            return response["data"]["keys"]
        except hvac.exceptions.InvalidPath:
            return []

    def audit_log(self, key: str) -> List[dict]:
        # Vault は監査ログを外部（syslog, file, etc.）に出すため、
        # アプリ側から直接取得するにはVault監査設定が必要
        return [{"note": "Audit logs should be configured on the Vault server."}]

    def rotate(self, key: str, new_value: str):
        self.set(key, new_value)
