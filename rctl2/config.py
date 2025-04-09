from typing import Optional

from pydantic import BaseModel


class Pipe(BaseModel):
    func: str
    params: dict = {}


class StoreConfig(BaseModel):
    opener: Pipe
    handler: Pipe | None = None


class Env(BaseModel):
    store_state: StoreConfig
    store_val: StoreConfig
    store_env: StoreConfig
    store_secret: StoreConfig


class ConfigMeta(BaseModel):
    version: str = "0.0.1"


class EnvirnomentConfig(BaseModel):
    config: ConfigMeta = ConfigMeta()
    services: dict[str, dict[str, Env]] = {}

    def get_target(self, service, target):
        _service = self.services[service]
        _target = _service[target]
        return _target
