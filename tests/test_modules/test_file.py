import pytest
from rctl.modules.mock import TrueOperator, FalseOperator
from rctl.modules.file import FsspecRootOperator, FsspecFileOperator, FsspecDirOperator
from rctl.modules.db import Psycopg2SchemaOperator
from rctl.modules._boto3 import PolicyController
from rctl.base2 import StepDataExtension
from rctl.base import Operator, Executable, HasOperator


def get_capability(cls: type):
    return {
        "create": hasattr(cls, "create"),
        "delete": hasattr(cls, "delete"),
        "exists": hasattr(cls, "exists"),
        "absent": hasattr(cls, "absent"),
    }


types = [FsspecRootOperator, TrueOperator, FalseOperator]


class PartialOperator:
    def __init__(self, operator: Operator, params: dict = None):
        self._operator = operator
        self._params = params or {}

    def to_executor(self):
        return self._operator.to_executor()

    def get_default_wait_time(self):
        return self._operator.get_default_wait_time()

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
    op = TrueOperator()
    assert op.create()[0]
    assert op.delete()[0]
    assert op.exists()[0]
    assert op.absent()[0]
    assert isinstance(op.get_default_wait_time(), (int, float))

    op = op.to_executor()
    assert op.created()
    assert op.deleted()
    assert op.exists()
    assert op.absent()
    assert op.recreated()

    op = FalseOperator()
    assert not op.create()[0]
    assert not op.delete()[0]
    assert not op.exists()[0]
    assert not op.absent()[0]
    assert isinstance(op.get_default_wait_time(), (int, float))

    op = op.to_executor()
    assert not op.created()
    assert not op.deleted()
    assert not op.exists()
    assert not op.absent()
    assert not op.recreated()


def test_dir():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        conn = {"protocol": "local"}
        params = {"bucket": td, "path": "file_dir"}
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
        params = {"bucket": td, "path": "file_test.txt"}
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


def test_s3_bucket_policy():
    conn = {
        "protocol": "s3",
        "endpoint_url": "http://localhost:9000",
        "key": "admin",
        "secret": "password",
    }
    params = {"bucket": "test-cache", "path": "testfile.txt"}
    op = PartialExecutor(FsspecFileOperator(**conn).to_executor(), params)
    assert op.created()

    conn = {
        "service_name": "s3",
        "endpoint_url": "http://localhost:9000",
        "aws_access_key_id": "admin",
        "aws_secret_access_key": "password",
    }
    params = {"bucket_name": "test-cache", "policy_name": "public"}
    op = PartialExecutor(PolicyController(**conn).to_executor(), params)
    assert op.created()


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
                path: "fsspec/s3/test.txt"
                content: "test"
        timeout: 100
        retry: 3
        wait_time: 0
    """

    step = StepDataExtension.from_stream(_).override(state="recreated")
    step.apply()
