import pytest
from src.modules.mock import TrueResource, FalseResource
from src.modules.file import FsspecRootOperator, FsspecFileOperator, FsspecDirOperator
from src.modules.db import Psycopg2SchemaOperator
from src.base2 import StepDataExtension
from src.base import Operator, Executable, HasOperator


def get_capability(cls: type):
    return {
        "create": hasattr(cls, "create"),
        "delete": hasattr(cls, "delete"),
        "exists": hasattr(cls, "exists"),
        "absent": hasattr(cls, "absent"),
    }


types = [FsspecRootOperator, TrueResource, FalseResource]


class PartialOperator:
    def __init__(self, operator: Operator, params):
        self._operator = operator
        self._params = params

    def exists(self):
        return self._operator.exists(**self._params)

    def absent(self):
        return self._operator.absent(**self._params)

    def create(self):
        return self._operator.create(**self._params)

    def delete(self):
        return self._operator.delete(**self._params)


class PartialExecutor:
    def __init__(self, operator: Executable, params):
        self._operator = operator
        self._params = params

    def exists(self):
        return self._operator.exists(**self._params)

    def absent(self):
        return self._operator.absent(**self._params)

    def created(self):
        return self._operator.created(**self._params)

    def deleted(self):
        return self._operator.deleted(**self._params)

    def recreated(self):
        return self._operator.recreated(**self._params)


@pytest.mark.parametrize("cls", types)
def test_exists_method(cls):
    methods = get_capability(cls)

    assert methods == {
        "create": True,
        "delete": True,
        "exists": True,
        "absent": True,
    }


def test_true_false():
    res = TrueResource()
    assert res.create()[0]
    assert res.delete()[0]
    assert res.exists()[0]
    assert res.absent()[0]
    assert isinstance(res.get_default_wait_time(), (int, float))

    res = res.to_executor()
    assert res.created()
    assert res.deleted()
    assert res.exists()
    assert res.absent()
    assert res.recreated()

    res = FalseResource()
    assert not res.create()[0]
    assert not res.delete()[0]
    assert not res.exists()[0]
    assert not res.absent()[0]
    assert isinstance(res.get_default_wait_time(), (int, float))

    res = res.to_executor()
    assert not res.created()
    assert not res.deleted()
    assert not res.exists()
    assert not res.absent()
    assert not res.recreated()


def test_dir():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        conn = {"protocol": "local"}
        params = {"path": td + "/file_dir", "bucket": ""}
        op = PartialExecutor(FsspecDirOperator(**conn).to_executor(), params)
        # base scenario
        print()
        assert not op.exists()
        assert op.absent()
        assert op.created()
        assert op.exists()
        assert not op.absent()
        assert op.deleted()
        assert not op.exists()
        assert op.absent()


def test_file():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        conn = {"protocol": "local"}
        params = {"path": td + "/file_test.txt", "bucket": ""}
        op = PartialExecutor(FsspecFileOperator(**conn).to_executor(), params)
        # base scenario
        print()
        assert not op.exists()
        assert op.absent()
        assert op.created()
        assert op.exists()
        assert not op.absent()
        assert op.deleted()
        assert not op.exists()
        assert op.absent()


def test_schema():
    conn = {
        "host": "localhost",
        "dbname": "dev",
        "user": "admin",
        "password": "password",
        "port": 5432,
    }
    params = {"schema": "resmanager"}
    op = PartialExecutor(Psycopg2SchemaOperator(**conn).to_executor(), params)

    # base scenario
    print()
    op.deleted()  # 残っている場合は削除
    assert not op.exists()
    assert op.absent()
    assert op.created()
    assert op.exists()
    assert not op.absent()
    assert op.deleted()
    assert not op.exists()
    assert op.absent()


def test_manifest():
    _ = """
    fsspec-local:
        description: "init"
        state: "recreated"
        connector:
            protocol: local
        module:
            type: fsspec
            subtype: file
            params:
                bucket: "test-cache"
                path: "fsspec/local/test.txt"
                content: "test!!!"
        wait_time: 0
    """

    step = StepDataExtension.from_stream(_).override(state="recreated")
    step.apply()

    _ = """
    postgres-schema:
        description: "init"
        state: "recreated"
        connector:
            host: localhost
            dbname: dev
            user: admin
            password: password
            port: 5432
        module:
            type: psycopg2
            subtype: schema
            params:
                schema: "resmanager"
        wait_time: 0
    """

    step = StepDataExtension.from_stream(_).override(state="recreated")
    step.apply()

    # dir の１つ目はバケットとみなされる
    _ = """
    fsspec-s3:
        description: "init"
        state: "recreated"
        connector:
            protocol: s3
            endpoint_url: http://localhost:9000
            key: admin
            secret: password
        module:
            type: fsspec
            subtype: file
            params:
                bucket: test-cache
                path: "fsspec/local/test.txt"
                content: "test"
        wait_time: 0
    """

    step = StepDataExtension.from_stream(_).override(state="recreated")
    step.apply()
