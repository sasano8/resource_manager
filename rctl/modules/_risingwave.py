from ..base import Operator
import psycopg2
from psycopg2 import sql
import traceback
from ..exceptions import NoRecordError
import psycopg2.extras


def format_value(value):
    if isinstance(value, str):
        return sql.Literal(value)  # 文字列は '...' にする
    return sql.SQL(str(value))  # 数値などはそのまま


def compile_with(with_option: dict):
    with_clause = sql.SQL(", ").join(
        sql.SQL("{}={}").format(sql.Identifier(k), format_value(v))
        for k, v in with_option.items()
    )
    query = sql.SQL("WITH ({})").format(with_clause)
    return query


def compile_create_sync(name, _from, with_option):
    with_stmt = compile_with(with_option)
    sync_stmt = sql.SQL("CREATE SINK IF NOT EXISTS {} FROM {} ".format(name, _from))
    return sync_stmt + with_stmt


def compile_create_source(name, with_option):
    with_stmt = compile_with(with_option)
    source_stmt = sql.SQL("CREATE SOURCE IF NOT EXISTS {} ".format(name))
    return source_stmt + with_stmt


def compile_create_subscription(name, _from, with_option):
    with_stmt = compile_with(with_option)
    ddl = (
        sql.SQL("CREATE SUBSCRIPTION IF NOT EXISTS {} FROM {} ".format(name, _from))
        + with_stmt
    )
    return ddl


def compile_drop(type, name):
    """type: SYNC, SOURCE, SUBSCRIPTION, TABLE, VIEW, MATERIALIZED VIEW ... any"""
    ddl = sql.SQL("DROP IF EXISTS {}".format(type, name))
    return ddl


def compile_exists(target: str, target_name: str, schema_name="public"):
    if target == "schema" or target == "db":
        raise NotImplementedError()

    table = {
        "table": "rw_catalog.rw_tables",
        "view": "rw_catalog.rw_views",
        "materialized_view": "rw_catalog.rw_materialized_views",
        "source": "rw_catalog.rw_sources",
        "subscription": "rw_catalog.rw_subscriptions",
        "sink": "rw_catalog.rw_sinks",
        "schema": "rw_catalog.rw_schemas",
    }.get(str.lower(target), None)

    if target is None:
        raise NotImplementedError()

    return sql.SQL(
        """
    SELECT
        s.name AS schema_name
        t.name AS target_name,
    FROM
        {TALBLE} t
    JOIN
        rw_catalog.rw_schemas s 
    ON
        t.schema_id = s.id
    WHERE
        LOWER(s.name) = %(SCHEMA_NAME)s
        AND LOWER(t.name) = %(TARGET_NAME)s
    """
    ).format(
        TABLE=sql.Identifier(table),
        SCHEMA_NAME=sql.Literal(str.lower(schema_name)),
        TARGET_NAME=sql.Literal(str.lower(target_name)),
    )


def _compile_exists(type, name):
    # SQLの標準規格
    """
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_name = 'your_table_name'
    )
    """

    # postgres 固有スキーマ(information_schema より細かい情報が見れるっぽい)
    """
    SELECT EXISTS (
      SELECT 1 FROM pg_catalog.pg_tables
      WHERE schemaname = 'public'
      AND tablename = 'your_table_name'
    )
    """

    """
    # コメントアウトしてるのは役に立たなそうなやつ
    rw_catalog.rw_materialized_views
    rw_catalog.rw_views
    rw_catalog.rw_sources
    rw_catalog.rw_tables
    rw_catalog.rw_system_tables
    rw_catalog.rw_subscriptions
    rw_catalog.rw_sinks
    rw_catalog.rw_columns
    rw_catalog.rw_databases
    rw_catalog.rw_connections
    rw_catalog.rw_users
    # rw_catalog.rw_secrets
    rw_catalog.rw_indexes
    rw_catalog.rw_iceberg_files
    rw_catalog.rw_user_secrets
    rw_catalog.rw_schemas
    rw_catalog.rw_types
    """

    """
    rw_catalog.rw_users
     id |   name   | is_super | create_db | create_user | can_login 
    ----+----------+----------+-----------+-------------+-----------
      2 | postgres | t        | t         | t           | t
      1 | root     | t        | t         | t           | t
    
    rw_catalog.rw_schemas
     id |        name        | owner |               acl               
    ----+--------------------+-------+---------------------------------
      3 | pg_catalog         |     1 | {postgres=UC/root,root=UC/root}
      4 | information_schema |     1 | {postgres=UC/root,root=UC/root}
      2 | public             |     1 | {postgres=UC/root,root=UC/root}
      5 | rw_catalog         |     1 | {postgres=UC/root,root=UC/root}

    rw_catalog.rw_databases
    id | name | owner |               acl               
    ----+------+-------+---------------------------------
     1 | dev  |     1 | {postgres=Cc/root,root=Cc/root}

    rw_catalog.rw_columns
     relation_id |              name              | position | is_hidden | is_primary_key | is_distribution_key | is_generated | generation_expression |        data_type         | type_oid | type_len |  udt_type   
    -------------+--------------------------------+----------+-----------+----------------+---------------------+--------------+-----------------------+--------------------------+----------+----------+-------------
      2147478665 | oid                            |        1 | f         | f              | f                   | f            |                       | integer                  |       23 |        4 | int4
      2147478665 | extname                        |        2 | f         | f              | f                   | f            |                       | character varying        |     1043 |       -1 | varchar

    select * from rw_catalog.rw_materialized_views
     id | name | schema_id | owner | definition | append_only | acl | initialized_at | created_at | initialized_at_cluster_version | created_at_cluster_version | background_ddl 
    select * from rw_catalog.rw_views
        id     |           name           | schema_id | owner | acl | definition |
    select * from rw_catalog.rw_sources
    id | name | schema_id | owner | connector | columns | format | row_encode | append_only | associated_table_id | connection_id | definition | acl | initialized_at | created_at | initialized_at_cluster_version | created_at_cluster_version | is_shared
    select * from rw_catalog.rw_tables
     id | name | schema_id | owner | definition | append_only | acl | initialized_at | created_at | initialized_at_cluster_version | created_at_cluster_version
    select * from rw_catalog.rw_subscriptions
     id | name | schema_id | owner | definition | acl | initialized_at | created_at | initialized_at_cluster_version | created_at_cluster_version 
    rw_catalog.rw_sinks
     id | name | schema_id | owner | connector | sink_type | connection_id | definition | acl | initialized_at | created_at | initialized_at_cluster_version | created_at_cluster_version 
    ----+------+-----------+-------+-----------+-----------+---------------+------------+-----+----------------+------------+--------------------------------+----------------------------
          
    """


class RisingwaveOperator(Operator):
    @staticmethod
    def get_operator(type: str):
        if type == "sync":
            return RisingwaveSyncOperator
        elif type == "source":
            return RisingwaveSourceOperator
        elif type == "subscription":
            return RisingwaveSubscriptionOperator
        elif type == "view":
            return NotImplementedError()
        else:
            raise TypeError()

    def __init__(self, host, dbname, user, password: str = "", port: int = 5432):
        self._dbparams = {
            "host": host,
            "dbname": dbname,
            "user": user,
            "password": password,
            "port": port,
        }

    def execute(self, stmt, params: tuple | dict = {}):
        # プレースホルダーの埋め込みはタプルと辞書のどっちか（位置とキーワードを混在できない）
        with psycopg2.connect(**self._dbparams) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(stmt, params)
                except Exception as e:
                    # return False, f"{str(e)}\n{traceback.format_exc()}"
                    raise
                return True, ""

    def scalar(self, stmt, params: tuple | dict = {}):
        with psycopg2.connect(**self._dbparams) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(stmt, params)
                except Exception as e:
                    # return False, f"{str(e)}\n{traceback.format_exc()}"
                    raise
                try:
                    row = cur.fetchone()
                except Exception as e:
                    raise
                    # return False, f"{str(e)}\n{traceback.format_exc()}"

                if not row:
                    raise NoRecordError("row does not exist.")
                    # return False, NoRecordError("row does not exist.")

                result = row[0]
                return result

    def all(self, stmt, params: tuple | dict = {}):
        with psycopg2.connect(**self._dbparams) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                try:
                    cur.execute(stmt, params)
                except Exception as e:
                    raise
                    # return False, f"{str(e)}\n{traceback.format_exc()}"

                try:
                    rows = cur.fetchall()
                except Exception as e:
                    raise
                    # return False, f"{str(e)}\n{traceback.format_exc()}"

                yield from rows

    def first_or_none(self, stmt, params: tuple | dict = {}):
        row = None
        for i, row in enumerate(self.all(stmt, params)):
            return row
        return row

    def one_or_none(self, stmt, params: tuple | dict = {}):
        row = None
        for i, row in enumerate(self.all(stmt, params)):
            if i > 1:
                raise Exception()
        return row

    def last_or_none(self, stmt, params: tuple | dict = {}):
        row = None
        for row in self.all(stmt, params):
            ...
        return row

    def exists(self, stmt, params: tuple | dict = {}):
        result = self.first_or_none(stmt, params)
        if result:
            return True
        else:
            return None


class RisingwaveSyncOperator(RisingwaveOperator):
    def create(self, name, _from, with_option: dict, schema: str = "public"):
        stmt = compile_create_sync(name, _from, with_option)
        ok, msg = self.execute(stmt)
        return ok, msg

    def delete(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_drop("SYNC", name)
        ok, msg = self.execute(stmt)
        return ok, msg

    def exists(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_exists("SYNC", name, schema)
        result = self.exists(stmt)
        return result, None

    def absent(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_exists("SYNC", name, schema)
        result = not self.exists(stmt)
        return result, None


class RisingwaveSourceOperator(RisingwaveOperator):
    def create(self, name, with_option: dict):
        stmt = compile_create_source(name, with_option)
        ok, msg = self.execute(stmt)
        return ok, msg

    def delete(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_drop("SOURCE", name)
        ok, msg = self.execute(stmt)
        return ok, msg

    def exists(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_exists("SOURCE", name, schema)
        result = self.exists(stmt)
        return result, None

    def absent(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_exists("SOURCE", name, schema)
        result = not self.exists(stmt)
        return result, None


class RisingwaveSubscriptionOperator(RisingwaveOperator):
    def create(self, name, _from, with_option: dict):
        stmt = compile_create_subscription(name, _from, with_option)
        ok, msg = self.execute(stmt)
        return ok, msg

    def delete(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_drop("SUBSCRIPTION", name)
        ok, msg = self.execute(stmt)
        return ok, msg

    def exists(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_exists("SUBSCRIPTION", name, schema)
        result = self.exists(stmt)
        return result, None

    def absent(self, name, schema: str = "public", *args, **kwargs):
        stmt = compile_exists("SUBSCRIPTION", name, schema)
        result = not self.exists(stmt)
        return result, None


class RisingwaveViewOperator(RisingwaveOperator): ...
