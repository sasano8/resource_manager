from typing import TypedDict
from time import sleep
from typing import Generator
import inspect
import traceback

ERROR_NOT_SUPPORT = "Not Supported Error"


class StepData(TypedDict):
    name: str
    description: str
    state: str
    module: str
    params: dict
    wait_time: float

class HasOperator:
    @classmethod
    def get_operator(cls, type: str):
        if type == "default":
            return cls
        else:
            raise TypeError()


class Operator(HasOperator):
    def to_executor(self):
        return Executable(self)

    def get_default_wait_time(self):
        return 0

    def create(self, **kwargs) -> tuple[bool, str]:
        return False, ERROR_NOT_SUPPORT

    def delete(self, **kwargs) -> tuple[bool, str]:
        return False, ERROR_NOT_SUPPORT

    def exists(self, **kwargs) -> tuple[bool, str]:
        return False, ERROR_NOT_SUPPORT

    def absent(self, **kwargs) -> tuple[bool, str]:
        return False, ERROR_NOT_SUPPORT


class ResourceController:
    def __init__(self, resource: Operator, wait_time: float):
        if not isinstance(resource, Operator):
            raise TypeError()
        self._resource = resource
        self._wait_time = wait_time

    def created(self, **kwargs):
        ok, err = yield self._resource.exists
        if ok:
            return
        ok, err = yield self._resource.create
        sleep(self._wait_time)
        ok, err = yield self._resource.exists

    def deleted(self, **kwargs):
        ok, err = yield self._resource.absent
        if ok:
            return
        ok, err = yield self._resource.delete
        sleep(self._wait_time)
        ok, err = yield self._resource.absent

    def exists(self, **kwargs):
        ok, err = yield self._resource.exists

    def absent(self, **kwargs):
        ok, err = yield self._resource.absent

    def recreated(self, **kwargs):
        ok, err = yield self.deleted
        ok, err = yield self.created


class Executable:
    def __init__(self, resource: Operator, wait_time: float = None):
        self._resource = resource

    def created(self, **params: dict):
        ok, msg = self.created_with_msg(**params)
        return ok

    def deleted(self, **params: dict):
        ok, msg = self.deleted_with_msg(**params)
        return ok

    def exists(self, **params: dict):
        ok, msg = self.exists_with_msg(**params)
        return ok

    def absent(self, **params: dict):
        ok, msg = self.absent_with_msg(**params)
        return ok

    def recreated(self, **params: dict):
        ok, msg = self.recreated_with_msg(**params)
        return ok

    def created_or_raise(self, **params: dict):
        ok, msg = self.created(**params)
        if not ok:
            raise Exception(msg)
        else:
            return ok

    def delete_or_raise(self, **params: dict):
        ok, msg = self.deleted(**params)
        if not ok:
            raise Exception(msg)
        else:
            return ok

    def exists_or_raise(self, **params: dict):
        ok, msg = self.exists(**params)
        if not ok:
            raise Exception(msg)
        else:
            return ok

    def absent_or_raise(self, **params: dict):
        ok, msg = self.absent(**params)
        if not ok:
            raise Exception(msg)
        else:
            return ok

    def recreated_or_raise(self, **params: dict):
        ok, msg = self.recreated(**params)
        if not ok:
            raise Exception(msg)
        else:
            return ok

    def created_with_msg(self, **params: dict):
        return execute(self._resource, "created", params)

    def deleted_with_msg(self, **params: dict):
        return execute(self._resource, "deleted", params)

    def exists_with_msg(self, **params: dict):
        return execute(self._resource, "exists", params)

    def absent_with_msg(self, **params: dict):
        return execute(self._resource, "absent", params)

    def recreated_with_msg(self, **params: dict):
        return execute(self._resource, "recreated", params)


def dummyhook(depth, func, ok, err): ...


def hook(depth, func, ok, err):
    print(" " * (depth * 2), func.__qualname__, ok, err)


def execute(
    resource: Operator,
    state: str,
    params: dict,
    massage: str = " must be {state} but: {str(err)}",
) -> tuple[bool, str]:
    wait_time = resource.get_default_wait_time()
    controller = ResourceController(resource, wait_time)
    generatable = getattr(controller, state)

    undefined = object()
    ok = undefined

    for depth, func, ok, err in execute_generator(generatable, params, 0):
        # print(" " * (depth * 2), func, ok, err)
        hook(depth, func, ok, err)

    # ok が更新されず、何も実行されなかった
    if ok is undefined:
        raise RuntimeError()

    return ok, err


def execute_generator(func, params: dict, depth=-1):
    depth = depth + 1
    if not inspect.isgeneratorfunction(func):
        try:
            if isinstance(func, tuple):
                raise Exception()

            ok, err = func(**params)
        except StopIteration as e:
            # 管理外の StopIteration を区別する
            raise RuntimeError("Unexpected StopIteration") from e
        except Exception as e:
            ok = False
            err = f"{str(e)}\n{traceback.format_exc()}"

        yield depth, func, ok, err
        return

    yield depth, func, None, "START"

    # is generator function
    gen: Generator = func(**params)
    next_func = next(gen)

    # 最低一つは要素が必要
    if not next_func:
        raise RuntimeError()

    try:
        while next_func:
            for child_depth, func, ok, err in execute_generator(
                next_func, params, depth
            ):
                yield child_depth, func, ok, err
            next_func = gen.send((ok, err))

    except StopIteration:
        ...
