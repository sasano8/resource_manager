import yaml
from pydantic import BaseModel

stores_toml = """
config:
    version: "0.1"

services:
    app1:
        default:
            store_val:
                opener:
                    func: "fsspec.open",
                    params:
                        urlpath = "s3://mybucket/myfile.toml"
                loader:
                    func: "tomllib.load"

            store_env:
                opener:
                    func: "fsspec.open",
                    params:
                        urlpath = "s3://mybucket/myfile.toml"
                loader:
                    func: "tomllib.load"

            store_secret:
                opener:
                    func: "fsspec.open",
                    params:
                        urlpath = "s3://mybucket/myfile.toml"
                loader:
                    func: "tomllib.load"
"""


# jsonnet
"""
local base = {
  url: "s3://mybucket/base.toml",
  retries: 3
};

{
  service1: base + {
    retries: 5
  },
  service2: base + {
    extra: true
  }
}
"""


class Pipe(BaseModel):
    func: str
    params: dict = {}


class StoreConfig(BaseModel):
    opener: Pipe
    loader: Pipe


class Env(BaseModel):
    store_val: StoreConfig
    store_env: StoreConfig
    store_secret: StoreConfig


class EnvirnomentConfig(BaseModel):
    config: dict = {}
    services: dict[str, dict[str, Env]] = {}

    def get_target(self, service, target):
        _service = self.services[service]
        _target = _service[target]
        return _target


def load_store_config_from_path(path, format: str = "yaml"):
    with open(path, "r") as f:
        config = load_store_config_from_str(f.read(), format)

    return config


def load_store_config_from_str(text: str, format: str = "yaml"):
    if format == "yaml":
        config = yaml.safe_load(text)
    else:
        raise NotImplementedError()

    parsed = EnvirnomentConfig(**config)
    return parsed
