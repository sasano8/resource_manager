import psycopg2
from psycopg2 import sql


class NoRecordError(Exception): ...


class Psycopg2Adapter:
    def __init__(self, host, dbname, user, password: str = "", port: int = 5432):
        self._dbparams = {
            "host": host,
            "dbname": dbname,
            "user": user,
            "password": password,
            "port": port,
        }

    def connect(self):
        return self.exists_db()

    def exists_db(self):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        with result as conn:
            ok, result = fetch_scalar(conn, "SELECT 1;")

        if ok:
            result = ""

        return ok, result

    def absent_db(self):
        ok, msg = self.exists_db()
        if ok:
            return False, "Not absent"
        else:
            return True, msg

    def exists_schema(self, schema_name):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        with result as conn:
            ok, result = fetch_scalar(
                conn,
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s);",
                (schema_name,),
            )
        if ok:
            if result == 1:
                return True, ""
            else:
                return False, f"Not exists {schema_name}"

    def absent_schema(self, schema_name):
        ok, msg = self.exists_schema(schema_name)
        if ok:
            return False, "Not absent."
        else:
            return True, msg

    def create_schema(self, schema_name):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        with result as conn:
            ok, msg = execute(
                conn,
                "CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};".format(
                    SCHEMA_NAME=sql.Identifier(schema_name)
                ),
            )
        if ok:
            return True, "Schema created."
        else:
            return False, msg

    def delete_schema(self, schema_name):
        ok, result = get_conn(self._dbparams)
        if not ok:
            return ok, result

        with result as conn:
            ok, msg = execute(
                conn,
                "DROP SCHEMA IF EXISTS {SCHEMA_NAME};".format(
                    SCHEMA_NAME=sql.Identifier(schema_name)
                ),
            )
        if ok:
            return True, "Schema created."
        else:
            return False, msg


def get_conn(dbparams):
    try:
        conn = psycopg2.connect(**dbparams)
    except Exception as e:
        return False, e
    return True, conn


def fetch_scalar(conn, stmt, params: tuple = tuple()):
    """スカラー値を返す"""
    with conn.cursor() as cur:
        try:
            cur.execute(sql.SQL(stmt), params)
        except Exception as e:
            return False, e

        try:
            row = cur.fetchone()
            if not row:
                return False, NoRecordError("row does not exist.")
            result = row[0]
        except Exception as e:
            return False, e
        return True, result


def execute(conn, stmt, params: tuple = tuple()):
    with conn.cursor() as cur:
        try:
            cur.execute(sql.SQL(stmt), params)
        except Exception as e:
            return False, e
        return True, ""


def assert_value(ok, result_or_error, expect, errmsg: str = "error"):
    if ok:
        ok = result_or_error == expect
        if ok:
            return ok, ""
        else:
            return False, errmsg
    else:
        return False, errmsg
