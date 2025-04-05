"""
rctl2パッケージの初期化処理を行うモジュール
"""

import logging
from typing import List, Optional

# ロガーの設定
logger = logging.getLogger(__name__)


def initialize() -> None:
    """
    rctl2パッケージの初期化処理を実行する

    この関数は以下の処理を行います：
    1. ファイルシステムの登録
    2. その他の初期化処理（将来的に追加予定）
    """
    logger.info("Initializing rctl2 package...")

    # ファイルシステムの登録
    _register_filesystems()

    # その他の初期化処理をここに追加
    # ...

    logger.info("rctl2 package initialization completed.")


def _register_filesystems() -> None:
    """
    fsspecにファイルシステム実装を登録する
    """
    from .filesystems import VaultFileSystem
    import fsspec

    logger.info("Registering filesystem implementations...")

    # Vaultファイルシステムの登録
    fsspec.register_implementation("vault", VaultFileSystem)

    logger.info("Filesystem implementations registered successfully.")
