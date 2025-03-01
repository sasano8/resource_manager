import json

try:
    import yaml
except Exception:
    ...

try:
    import hcl2
except Exception:
    ...


def from_json(path: str):
    with open(path) as f:
        data = yaml.safe_load(path)
    return data


def from_yml(path: str):
    with open(path) as f:
        data = yaml.safe_load(path)
    return data


def from_hcl(path: str):
    with open(path) as f:
        data = hcl2.load(f)
    return data
