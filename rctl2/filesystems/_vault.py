import json
from io import BytesIO, StringIO
from typing import Any, BinaryIO, Dict, TextIO

import fsspec
import hvac
from hvac.exceptions import InvalidPath

from ..exceptions import AppError
from .utils import normalize_path


class VaultWriteIO:
    """Vaultへの書き込み操作を扱うためのI/Oクラス"""

    def __init__(self, fs, path: str, mode: str = "w"):
        """VaultWriteIOの初期化

        Parameters
        ----------
        fs : VaultFileSystem
            VaultFileSystemのインスタンス
        path : str
            書き込み先のパス
        mode : str, optional
            書き込みモード ('w' または 'wb'), by default "w"
        """
        self.fs = fs
        self.path = path
        self.mode = mode
        self.buffer = BytesIO() if mode == "rb" else StringIO()
        self.closed = False

    def write(self, data: str | bytes) -> int:
        """データをバッファに書き込む

        Parameters
        ----------
        data : Union[str, bytes]
            書き込むデータ

        Returns:
        -------
        int
            書き込まれたバイト数
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.buffer.write(data)

    def read(self, size: int = -1) -> str | bytes:
        """バッファからデータを読み込む

        Parameters
        ----------
        size : int, optional
            読み込むサイズ, by default -1 (すべて読み込む)

        Returns:
        -------
        Union[str, bytes]
            読み込まれたデータ
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.buffer.read(size)

    def flush(self):
        """バッファをフラッシュする"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self.buffer.flush()

    def close(self):
        """ファイルを閉じる。この時点でVaultにデータが書き込まれる"""
        if self.closed:
            return

        self.flush()
        content = self.buffer.getvalue()
        self.buffer.close()
        self.closed = True

        # バイナリモードの場合はデコード
        if self.mode == "rb":
            content = content.decode("utf-8")

        # VaultFileSystemのメソッドを使用してVaultに書き込む
        self.fs._write_secret(self.path, content)

    def __enter__(self):
        """コンテキストマネージャのエントリーポイント

        Returns:
        -------
        VaultWriteIO
            自身のインスタンス
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャのエグジットポイント

        Parameters
        ----------
        exc_type : type
            例外の型
        exc_val : Exception
            例外のインスタンス
        exc_tb : traceback
            例外のトレースバック
        """
        self.close()


def exclude_none(data: dict):
    return {k: v for k, v in data.items() if v is not None}


class VaultFileSystem(fsspec.AbstractFileSystem):
    """HashiCorp Vaultをファイルシステムとして扱うためのfsspec実装"""

    protocol = "vault"

    def __init__(
        self,
        mount_point,
        # 直接clientを指定する場合
        client=None,
        # hvac.Clientの引数
        url=None,
        token=None,
        cert=None,
        verify=None,
        timeout=None,
        proxies=None,
        allow_redirects=None,
        session=None,
        adapter=None,
        namespace=None,
        # fsspec の引数
        **kwargs,
    ):
        """VaultFileSystemの初期化

        Parameters
        ----------
        mount_point : str, optional
            KVシークレットエンジンのマウントポイント, by default "secret"
        client : hvac.Client, optional
            既存のVaultクライアント
        url : str, optional
            VaultサーバーのURL
        token : str, optional
            Vaultの認証トークン
        # hvac.Clientの引数
        cert : tuple, optional
            クライアント証明書のパスとキーパス
        verify : bool, optional
            SSL証明書の検証を行うかどうか
        timeout : int, optional
            タイムアウト時間（秒）
        proxies : dict, optional
            プロキシ設定
        allow_redirects : bool, optional
            リダイレクトを許可するかどうか
        session : requests.Session, optional
            既存のセッション
        adapter : class, optional
            アダプタークラス
        namespace : str, optional
            名前空間
        # fsspecの引数
        **kwargs : dict
            その他のパラメータ

        Raises:
            ValueError: クライアントが提供されている場合にURLまたはトークンが指定されている場合
            ValueError: クライアント、URL、トークンのいずれも提供されていない場合
            ConnectionError: Vaultサーバーに接続できない場合
        """
        # fsspecの初期化
        super().__init__(**kwargs)

        # hvac.Clientの引数を準備
        hvac_kwargs = {
            "url": url,
            "token": token,
            "cert": cert,
            "verify": verify,
            "timeout": timeout,
            "proxies": proxies,
            "allow_redirects": allow_redirects,
            "session": session,
            "adapter": adapter,
            "namespace": namespace,
        }

        hvac_kwargs = exclude_none(hvac_kwargs)

        if client and len(hvac_kwargs):
            raise ValueError(
                "When providing a client, url and token parameters should not be provided"
            )

        if client:
            self.client = client
        else:
            self.client = hvac.Client(**hvac_kwargs)

        self.mount_point = mount_point

    @classmethod
    def from_client(cls, mount_point, client, **kwargs):
        """既存のVaultクライアントからVaultFileSystemを作成する

        Parameters
        ----------
        client : hvac.Client
            既存のVaultクライアント
        mount_point : str, optional
            シークレットエンジンのマウントポイント, by default "secret"
        **kwargs
            その他のパラメータ

        Returns:
        -------
        VaultFileSystem
            作成されたVaultFileSystemインスタンス
        """
        return cls(mount_point=mount_point, client=client, **kwargs)

    @classmethod
    def from_url(
        cls,
        mount_point,
        url,
        token,
        cert=None,
        verify=None,
        timeout=None,
        proxies=None,
        allow_redirects=None,
        session=None,
        adapter=None,
        namespace=None,
        **kwargs,
    ):
        """URLとトークンからVaultFileSystemを作成する

        Parameters
        ----------
        url : str
            VaultサーバーのURL
        token : str
            Vaultの認証トークン
        cert : tuple, optional
            クライアント証明書のパスとキーパス
        verify : bool, optional
            SSL証明書の検証を行うかどうか
        timeout : int, optional
            タイムアウト時間（秒）
        proxies : dict, optional
            プロキシ設定
        allow_redirects : bool, optional
            リダイレクトを許可するかどうか
        session : requests.Session, optional
            既存のセッション
        adapter : class, optional
            アダプタークラス
        namespace : str, optional
            名前空間
        mount_point : str, optional
            KVシークレットエンジンのマウントポイント, by default "secret"
        **kwargs
            その他のパラメータ

        Returns:
        -------
        VaultFileSystem
            作成されたVaultFileSystemインスタンス
        """
        return cls(
            mount_point=mount_point,
            url=url,
            token=token,
            cert=cert,
            verify=verify,
            timeout=timeout,
            proxies=proxies,
            allow_redirects=allow_redirects,
            session=session,
            adapter=adapter,
            namespace=namespace,
            **kwargs,
        )

    def _authenticate(self):
        """Vaultサーバーに接続する"""
        try:
            return self.client.is_authenticated()
        except Exception as e:
            raise AppError(f"Authentication failed: {self.client.url}") from e

    def is_authenticated(self) -> bool:
        """Vaultサーバーへの認証状態を確認する

        Returns:
        -------
        bool
            認証されている場合はTrue、そうでない場合はFalse
        """
        try:
            return self._authenticate()
        except AppError:
            return False

    def _normalize_path(self, path):
        """パスを正規化する"""
        return normalize_path(path)

    # 参照がないので削除
    # def _path_to_key(self, path: str) -> str:
    #     """ファイルシステムのパスをVaultのキーに変換する"""
    #     return self._normalize_path(path)

    # 変化がない実装なので無効か
    # def _key_to_path(self, key: str) -> str:
    #     """Vaultのキーをファイルシステムのパスに変換する"""
    #     return f"{key}"

    def _read_secret(self, path: str) -> Dict[str, Any]:
        """Vaultからシークレットを読み取る

        Parameters
        ----------
        path : str
            読み取るパス

        Returns:
        -------
        Dict[str, Any]
            Vaultからの応答

        Raises:
        ------
        FileNotFoundError
            パスが存在しない場合
        """
        try:
            return self.client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=self.mount_point, raise_on_deleted_version=True
            )
        except Exception as e:
            raise FileNotFoundError(f"Secret not found: {path}") from e

    def _write_secret(self, path: str, content: str) -> None:
        """Vaultにシークレットを書き込む

        Parameters
        ----------
        path : str
            書き込むパス
        content : str
            書き込む内容
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {"value": content}

        self.client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=data, mount_point=self.mount_point
        )

    def _ls(self, path: str, detail: bool = True, **kwargs):
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path, mount_point=self.mount_point
            )
            items: list[str] = response["data"]["keys"]
        except InvalidPath:
            # 一つも存在しない場合、InvalidPath が返る
            items = []

        if detail:
            for child in items:
                key = f"{path.strip('/')}/{child}"
                if key.endswith("/"):
                    yield self._info_dir(key)
                else:
                    yield self.info(key)
        else:
            yield from items

    def ls(self, path: str, detail: bool = True, **kwargs) -> list[str] | list[dict]:
        """指定されたパスの内容をリストする

        Parameters
        ----------
        path : str
            リストするパス
        detail : bool, optional
            詳細情報を返すかどうか, by default True

        Returns:
        -------
        List[Union[str, Dict[str, Any]]]
            パスの内容
        """
        return [x for x in self._ls(path, detail, **kwargs)]

    def _find(self, path: str, countdown: int):
        countdown -= 1
        if countdown < 0:
            return
        for x in self._ls(path, detail=True):
            if x["name"].endswith("/"):
                yield from self._find(x["name"], countdown=countdown)
            else:
                yield x

    def _find2(self, path: str, maxdepth: int, withdirs=False, detail=False):
        maxdepth = maxdepth or float("inf")

        for x in self._find(path, maxdepth):
            if not withdirs:
                if x["name"].endswith("/"):
                    continue

            if detail:
                yield x
            else:
                yield x["name"]

    def find(self, path: str, maxdepth=None, withdirs=False, detail=False):
        return [
            x
            for x in self._find2(
                path, maxdepth=maxdepth, withdirs=withdirs, detail=detail
            )
        ]

    def _info_dir(self, path: str) -> Dict[str, Any]:
        """与えたパスをディレクトリとみなして、構造を返す"""
        # normalized_path = self._normalize_path(path)
        return {"name": path.strip("/") + "/", "size": None, "type": "dir"}

    def info(self, path: str) -> Dict[str, Any]:
        """指定されたパスの情報を取得する

        Parameters
        ----------
        path : str
            情報を取得するパス

        Returns:
        -------
        Dict[str, Any]
            パスの情報
        """
        # normalized_path = self._normalize_path(path)
        try:
            metadata = self.client.secrets.kv.v2.read_secret_metadata(
                path=path, mount_point=self.mount_point
            )
            created_time = metadata["data"]["created_time"]
            return {
                "name": path.strip("/"),
                "size": None,
                "type": "file",
                "created": created_time,
                "modified": created_time,
            }
        except Exception as e:
            raise FileNotFoundError(f"File not found: {path}") from e

    def exists(self, path: str) -> bool:
        """指定されたパスが存在するかどうかを確認する

        Parameters
        ----------
        path : str
            確認するパス

        Returns:
        -------
        bool
            パスが存在するかどうか
        """
        try:
            normalized_path = self._normalize_path(path)
            self.client.secrets.kv.v2.read_secret_metadata(
                path=normalized_path, mount_point=self.mount_point
            )
            return True
        except Exception:
            return False

    def rm(self, path: str, recursive: bool = False, **kwargs):
        """指定されたパスを削除する

        Parameters
        ----------
        path : str
            削除するパス
        recursive : bool, optional
            再帰的に削除するかどうか, by default False
        **kwargs : dict
            その他のパラメータ
        """
        if recursive:
            raise NotImplementedError()

        normalized_path = self._normalize_path(path)

        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=normalized_path, mount_point=self.mount_point
            )
        except Exception as e:
            raise FileNotFoundError(f"File not found: {path}") from e

    def open(
        self, path: str, mode: str = "rb", block_size: int | None = None, **kwargs
    ) -> BinaryIO | TextIO:
        """指定されたパスを開く

        Parameters
        ----------
        path : str
            開くパス
        mode : str, optional
            開くモード, by default 'rb'
            サポートされるモード: 'r', 'rb', 'w', 'wb'
        block_size : Optional[int], optional
            ブロックサイズ, by default None
        **kwargs : dict
            その他のパラメータ

        Returns:
        -------
        Union[BinaryIO, TextIO]
            ファイルオブジェクト

        Raises:
        ------
        ValueError
            サポートされていないモードが指定された場合
        """
        # normalized_path = self._normalize_path(path)

        # サポートされるモードを明示的に制限
        if mode not in ["r", "rb", "w", "wb"]:
            raise ValueError(
                f"Unsupported mode: {mode}. Supported modes are 'r', 'rb', 'w', 'wb'"
            )

        if mode in ["r", "rb"]:
            # 読み取りモード
            try:
                response = self._read_secret(path)
                dumped = json.dumps(response["data"]["data"])

                # Vaultの応答をそのまま返す
                if mode == "rb":
                    return BytesIO(dumped.encode())
                else:
                    return StringIO(dumped)
            except Exception as e:
                raise FileNotFoundError(f"File not found: {path}") from e
        else:  # mode in ['w', 'wb']
            # 書き込みモード
            return VaultWriteIO(self, path, mode)
