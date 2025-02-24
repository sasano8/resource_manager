from ..base import Resource

import psycopg2
from psycopg2 import sql

db_params = {
    "dbname": "your_database",
    "user": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": 5432,
}


class SqlalchemySchema(Resource):
    def __init__(self, schema: str):
        raise NotImplementedError()
        self._schema = schema

    def create(self):
        f"CREATE SCHEMA IF NOT EXISTS {self._schema}"
        return True, ""

    def delete(self):
        f"DROP SCHEMA IF EXISTS {self._schema}"
        return True, ""

    def exists(self):
        "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s);"
        if self._path.exists():
            return True, ""
        else:
            return False, f"Not Exists {str(self._path)}"

    def absent(self):
        "SELECT NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s);"
        if self._path.exists():
            return False, f"Exists {str(self._path)}"
        else:
            return True, ""


def aaa():
    import psycopg2
    from psycopg2 import sql

    # データベース接続設定
    db_params = {
        "dbname": "your_database",
        "user": "your_username",
        "password": "your_password",
        "host": "localhost",
        "port": 5432,
    }

    # 確認したいスキーマ名
    schema_name = "my_schema"

    # PostgreSQLに接続
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                # スキーマ存在確認のクエリ
                cur.execute(
                    sql.SQL(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s);"
                    ),
                    (schema_name,),
                )

                # 結果を取得
                exists = cur.fetchone()[0]

                # 結果を表示
                if exists:
                    print(f"スキーマ '{schema_name}' は存在します。")
                else:
                    print(f"スキーマ '{schema_name}' は存在しません。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
