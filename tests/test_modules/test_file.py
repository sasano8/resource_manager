import pytest
from src.modules.mock import TrueResource, FalseResource
from src.modules.file import FsspecDefaultOperator, FsspecFileOperator
from src.base2 import StepDataExtension
from src.base import Resource, Executable, HasOperator


def get_capability(cls: type):
    return {
        "create": hasattr(cls, "create"),
        "delete": hasattr(cls, "delete"),
        "exists": hasattr(cls, "exists"),
        "absent": hasattr(cls, "absent"),
    }


types = [FsspecDefaultOperator, TrueResource, FalseResource]


class PartialOperator:
    def __init__(self, operator: Resource, params):
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


def test_file():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        params = {"path": td + "/file_test.txt"}
        res = PartialExecutor(FsspecFileOperator("local").to_executor(), params)
        # base scenario
        print()
        assert not res.exists()
        assert res.absent()
        assert res.created()
        assert res.exists()
        assert not res.absent()
        assert res.deleted()
        assert not res.exists()
        assert res.absent()


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
                path: ".cache/fsspec/local/test.txt"
                content: "test!!!"
        wait_time: 0
    """

    step = StepDataExtension.from_stream(_).override(state="created")
    step.apply()
