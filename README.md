# rctl

接続情報、機密情報の管理や、リソースの状態管理が面倒だ。
そういったものを管理できる仕組みを作る。

## init

リソースを初期化する。すでに準備済みのリソースに対しては何もしない。

## destroy

リソースを削除。存在しない場合は無視します。

## recreate

destroy 実行後に、init を実行します。



# 開発に貢献する

```
make sync-dev
```

```
pre-commit install
```


# CLI

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
