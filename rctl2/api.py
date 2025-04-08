from typing import Tuple

from . import config


class Result(Tuple[int, str]):
    def __new__(cls, ok: int, msg: str):
        return super().__new__(cls, (ok, msg))

    @classmethod
    def ok(cls, msg=None):
        return cls(1, msg)

    @classmethod
    def err(cls, msg: str = None):
        return cls(0, msg)

    @classmethod
    def create(cls, ok: int | bool, msg: str = None):
        _ok = int(ok)
        if _ok:
            return cls(ok, None)
        else:
            return cls(ok, msg)

    def __bool__(self):
        return bool(self[0])

    def dispatch(self, on_ok, on_err):
        if self[0]:
            result = on_ok(self[1])
        else:
            result = on_err(self[1])

        if isinstance(result, Exception):
            raise result
        else:
            return result


class RctlWorkSpace:
    PATH_CONFIG_DEFAULT = ".cache/rctl/config.yml"

    def __init__(self, config: config.EnvirnomentConfig):
        self._config = config

    @classmethod
    def config_init(cls, app_name: str = None, env_name: str = "default"):
        if not app_name:
            import os

            app_name = os.path.basename(os.getcwd())

        conf = config.EnvirnomentConfig(
            config=config.ConfigMeta(),
            services={
                app_name: {
                    env_name: config.Env(
                        store_state=config.StoreConfig(
                            opener=config.Pipe(
                                func="fsspec.open",
                                params={
                                    "urlpath": f"file://./.cache/rctl/envs/{app_name}/state.yml"
                                },
                            ),
                            handler=config.Pipe(func="yaml"),
                        ),
                        store_env=config.StoreConfig(
                            opener=config.Pipe(
                                func="os.envirnoment",
                            ),
                        ),
                        store_secret=config.StoreConfig(
                            opener=config.Pipe(
                                func="fsspec.open",
                                params={
                                    "urlpath": f"file://./.cache/rctl/envs/{app_name}/secrets.yml"
                                },
                            ),
                            handler=config.Pipe(func="yaml"),
                        ),
                        store_val=config.StoreConfig(
                            opener=config.Pipe(
                                func="fsspec.open",
                                params={
                                    "urlpath": f"file://./.cache/rctl/envs/{app_name}/vals.yml"
                                },
                            ),
                            handler=config.Pipe(func="yaml"),
                        ),
                    )
                }
            },
        )
        return cls(conf)

    @classmethod
    def config_load(cls, path: str = PATH_CONFIG_DEFAULT):
        import yaml

        with open(path, "r") as f:
            conf = yaml.safe_load(f)

        if isinstance(conf, config.EnvirnomentConfig):
            return cls(conf)
        elif isinstance(conf, dict):
            obj = config.EnvirnomentConfig(**conf)
            return cls(obj)
        else:
            raise NotImplementedError()

    def config_save(self, path: str = PATH_CONFIG_DEFAULT, override: bool = False):
        if not override:
            import os

            if os.path.exists(path):
                return Result.err(f"File already exists: {path}")

        import yaml

        data = self._config.model_dump()
        with open(path, "w") as f:
            yaml.dump(data, f)

        return Result.ok(f"The config was saved in: {path}")

    @classmethod
    def config_exists(cls, path: str = PATH_CONFIG_DEFAULT):
        import os

        if not os.path.exists(path):
            return Result.err(f"File not found: {path}")

        if not os.path.isfile(path):
            return Result.err(f"Is not file: {path}")

        return Result.ok()

    def config_show(self):
        from io import StringIO

        import yaml

        data = self._config.model_dump()

        with StringIO() as f:
            yaml.dump(data, f)
            f.seek(0)
            return f.read()
