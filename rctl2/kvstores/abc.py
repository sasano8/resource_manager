Undefined = object()


class AbstractKVStore:
    def flush(self): ...


def load_from_fsspec(urlpath, format: str = "yaml", **kwargs):
    import fsspec

    if format == "yaml":
        import yaml

        with fsspec.open(urlpath, mode="r", **kwargs) as f:
            data = yaml.safe_load(f)
    else:
        raise NotImplementedError()

    return data


def load_from_env():
    import os

    return dict(os.environ)
