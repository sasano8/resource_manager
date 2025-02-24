import yaml
from .base import StepData, Resource, execute, HasOperator
from .registry import _registry


class StepDataExtension:
    def __init__(self, step: StepData):
        self._step = self.validate(step)

    @classmethod
    def from_file(cls, path: str):
        with open(path, "r") as f:
            return cls.from_stream(f)

    @classmethod
    def _load_from_stream(cls, stream):
        data = yaml.safe_load(stream)

        if not isinstance(data, dict):
            raise TypeError("dict型")

        if len(data) != 1:
            raise TypeError("ルート要素は１つ")

        key = list(data.keys())[0]
        v = data[key]
        v["id"] = key
        return v

    @classmethod
    def from_stream(cls, stream):
        data = cls._load_from_stream(stream)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(StepData(**data))

    @classmethod
    def validate(cls, data: StepData):
        state = data["state"]
        if state not in {"created", "deleted", "exists", "absent", "recreated"}:
            raise ValueError(state)

        return data

    def override(self, state: str):
        new_value = {**self._step, "state": state}
        return StepDataExtension(new_value)

    def apply(self, massage: str = " must be {state} but: {str(err)}"):
        step = self._step
        state = step["state"]
        connector = step.get("connector", {})
        step["module"] = Module.validate(step["module"])

        res_cls: HasOperator = _registry.get_cls(step["module"]["type"])
        if not res_cls:
            raise RuntimeError()
        
        operator_cls = res_cls.get_operator(step["module"]["subtype"])
        operator: Resource = operator_cls(**connector)
        executor = CliExecutor()
        return executor.execute(operator, state, step["module"]["params"])

class Module:
    @classmethod
    def validate(cls, data: dict):
        if not isinstance(data, dict):
            raise TypeError()
        
        new_data = {
            "type": data.get("type", ""),
            "subtype": data.get("subtype", "default"),
            "params": data.get("params", {})
        }

        if not new_data["type"]:
            raise TypeError()

        return new_data



class CliExecutor:
    def execute(
        self,
        resource: Resource,
        state: str,
        params: dict = None,
        massage: str = " must be {state} but: {err}",
    ):
        params = params or {}
        ok, msg = execute(resource, state, params)
        if not ok:
            msg = massage.format(state=state, err=str(msg))
            raise Exception(msg)
