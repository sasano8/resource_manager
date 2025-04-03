"""
env1:
    protocol:
        type: env
    serializer:
        type: null
    params:
        root: ""
        prefix: ""
        cache: true

env2:
    protocol:
        type: file
    serializer:
        type: yaml
    params:
        root: ""

env3:
    protocol:
        type: dict
        options:
            src: {"a": 1}
    serializer:
        type: null
"""


def create_from_path(config_path):
    data = {}
    return create_from_dict(data)


def create_from_dict(): ...
