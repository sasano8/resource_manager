import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.data = {}

    logger.info("💡 DB initialized")
    yield
    app.state.db.clear()  # 終了処理


class AppContext:
    def __init__(self, data: dict):
        self._data = data

    def get_db(self):
        return ""

    def get_fs(self):
        return ""


app = FastAPI()


def get_dp(app: FastAPI = app):
    yield AppContext(app.state.data)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/{envirnoment}/connectors")
def list_connectors(envirnoment: str):
    return [
        {
            "name": "postgres-1",
            "type": "psycopg2",
            "params": {
                "dbname": "{{ db_name | default('dev') }}",
                "user": "{{ db_user | default('admin') }}",
                "password": "{{ db_password | default('password') }}",
                "host": "{{ db_host | default('localhost') }}",
                "port": "{{ db_port | default(5432) }}",
            },
        }
    ]


@app.get("/{envirnoment}/resources")
def list_resources(envirnoment: str):
    return [
        {
            "name": "mlflow-postgres",
            "description": "init",
            "state": "created",
            "module": "file",
            "connector": {"ref": "fsspec-local"},
            "params": {"path": "test.txt", "content": "test"},
        }
    ]


@app.get("/{envirnoment}/status")
def list_status(envirnoment: str):
    return [
        {
            "name": "mlflow-postgres",
            "expected": "created",
            "actual": "absent",
            "message": "",
            "last_check_at": "1970-01-01T00:00:00Z",
        }
    ]
