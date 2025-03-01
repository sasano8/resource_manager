from ..base import Operator
from ..exceptions import NoRecordError

import psycopg2
from psycopg2 import sql
import traceback


class Psycopg2SchemaOperator(Operator):
    @staticmethod
    def get_operator(type: str):
        if type == "schema":
            return Psycopg2SchemaOperator
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

    def exists(self, schema, *args, **kwargs):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        stmt = sql.SQL(
            "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s);"
        )

        with result as conn:
            ok, result = fetch_scalar(
                conn,
                stmt,
                (schema,),
            )
        if ok:
            if result == 1:
                return True, ""
            else:
                return False, f"Not exists {schema}"

    def absent(self, schema, *args, **kwargs):
        ok, msg = self.exists(schema)
        if ok:
            return False, "Not absent."
        else:
            return True, msg

    def create(self, schema, *args, **kwargs):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        stmt = sql.SQL("CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};").format(
            SCHEMA_NAME=sql.Identifier(schema)
        )

        with result as conn:
            ok, msg = execute(
                conn,
                stmt,
            )
        if ok:
            return True, "Schema created."
        else:
            return False, msg

    def delete(self, schema, *args, **kwargs):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        stmt = sql.SQL("DROP SCHEMA IF EXISTS {SCHEMA_NAME};").format(
            SCHEMA_NAME=sql.Identifier(schema)
        )

        with result as conn:
            ok, msg = execute(
                conn,
                stmt,
            )
        if ok:
            return True, "Schema created."
        else:
            return False, msg


def get_conn(dbparams):
    try:
        conn = psycopg2.connect(**dbparams)
    except Exception as e:
        return False, f"{str(e)}\n{traceback.format_exc()}"
    return True, conn


def fetch_scalar(conn, stmt, params: tuple = tuple()):
    """スカラー値を返す"""
    with conn.cursor() as cur:
        try:
            cur.execute(stmt, params)
        except Exception as e:
            return False, f"{str(e)}\n{traceback.format_exc()}"

        try:
            row = cur.fetchone()
            if not row:
                return False, NoRecordError("row does not exist.")
            result = row[0]
        except Exception as e:
            return False, f"{str(e)}\n{traceback.format_exc()}"
        return True, result


def execute(conn, stmt, params: tuple = tuple()):
    with conn.cursor() as cur:
        try:
            cur.execute(stmt, params)
        except Exception as e:
            return False, f"{str(e)}\n{traceback.format_exc()}"
        return True, ""
