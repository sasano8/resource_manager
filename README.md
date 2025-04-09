# rctl

## 開発に貢献する

仮想環境を構築します。

```
make sync-dev
```

プレコミットを構成します。

```
make install-precommit
```

ライブラリをインストールします（VaultFileSystem が fsspec のエントリーポイントに登録されます）。

```
make install
```

コードをフォーマットします。

```
make format
```

テストを実行します。

```
make test
```

## 入門 

```
import fsspec

fs = fsspec.filesystem("vault", mount_point="secret", url="http://127.0.0.1:8200", token="vaulttoken")
```


## 概念

接続情報、機密情報の管理や、リソースの状態管理が面倒だ。
そういったものを管理できる仕組みを作る。

### init

リソースを初期化する。すでに準備済みのリソースに対しては何もしない。

### destroy

リソースを削除。存在しない場合は無視します。

### recreate

destroy 実行後に、init を実行します。


## CLI

```
uv tool run rctl
```

次のようにリソースの状態を適用することができます。
指定するパスがディレクトリの場合、再帰的に yml ファイルを読み取りリソースの状態を適用します。

```
rctl resource apply -f resources/
```

- は標準入力から読み取るという docker で用意された機能

```
printf "mysecretdata" | docker secret create my_secret -
```


```


