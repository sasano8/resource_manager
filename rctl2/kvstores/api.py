"""env1:
    store:
        type: env
    serializer:
        type: null
    params:
        root: ""
        prefix: ""

env2:
    store:
        type: fsspec
    serializer:
        type: yaml
    params:
        root: ""

env3:
    store:
        type: dict
        params:
            src: "env2"  # 別のストアをソースとして参照可能（キャッシュとして機能）
    serializer:
        type: null
"""


def create_from_path(config_path):
    data = {}
    return create_from_dict(data)


def create_from_dict(): ...
