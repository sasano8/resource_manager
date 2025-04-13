import datetime

import pytest

from rctl2.serializers import (
    JsonSerializer,
    MultiSerializer,
    NullSerializer,
    TomlSerializer,
    YamlSerializer,
)


def test_null_serializer():
    """そのままオブジェクトが返るシリアライザーのテストを行う"""
    sl = NullSerializer()
    assert sl.loads("1") == "1"
    assert sl.loads('"a"') == '"a"'
    assert sl.loads({}) == {}
    assert sl.loads([]) == []

    assert sl.dumps("1") == "1"
    assert sl.dumps('"a"') == '"a"'
    assert sl.dumps({}) == {}
    assert sl.dumps([]) == []


def test_json_serializer():
    sl = JsonSerializer()
    assert sl.loads("1") == 1
    assert sl.loads('"a"') == "a"
    assert sl.loads("{}") == {}
    assert sl.loads("[]") == []

    assert sl.dumps(1) == "1"
    assert sl.dumps("a") == '"a"'
    assert sl.dumps({}) == "{}"
    assert sl.dumps([]) == "[]"


def test_yaml_serializer():
    sl = YamlSerializer()
    assert sl.loads("1") == 1
    assert sl.loads('"a"') == "a"
    assert sl.loads("{}") == {}
    assert sl.loads("[]") == []
    assert sl.loads("2023-01-01T12:34:56+09:00") == datetime.datetime(
        2023,
        1,
        1,
        12,
        34,
        56,
        tzinfo=datetime.timezone(datetime.timedelta(seconds=32400)),
    )

    # ... は終端記号
    assert sl.dumps(1) == "1\n...\n"
    assert sl.dumps("a") == "a\n...\n"
    assert sl.dumps({}) == "{}\n"
    assert sl.dumps([]) == "[]\n"

    assert sl.loads("1\n...\n") == 1
    assert sl.loads("a\n...\n") == "a"


def test_toml_serializer():
    sl = TomlSerializer()
    # Toml のトップレベルはキーバリューペア
    assert sl.loads("value = 1") == {"value": 1}
    assert sl.loads('value = "a"') == {"value": "a"}
    assert sl.loads("value = 1.5") == {"value": 1.5}
    assert sl.loads("value = {}") == {"value": {}}
    assert sl.loads("value = []") == {"value": []}
    assert sl.loads("value = 2023-01-01T12:34:56+09:00") == {
        "value": datetime.datetime(
            2023,
            1,
            1,
            12,
            34,
            56,
            tzinfo=datetime.timezone(datetime.timedelta(seconds=32400)),
        )
    }

    # dumps は未サポート


def test_multi_serializer():
    assert MultiSerializer._make_index() == {}

    null = NullSerializer()
    json = JsonSerializer()
    yaml = YamlSerializer()

    assert MultiSerializer._make_index(null) == {"null": null}
    assert MultiSerializer._make_index(json) == {"json": json}
    assert MultiSerializer._make_index(yaml) == {"yml": yaml, "yaml": yaml}
    assert MultiSerializer._make_index(null, json, yaml) == {
        "yml": yaml,
        "yaml": yaml,
        "json": json,
        "null": null,
    }

    sl = MultiSerializer.from_serializers(null, json, yaml)

    # 指定した形式でロードできること
    assert sl.loads('"a"', extension="null") == '"a"'
    assert sl.loads('"a"', extension="json") == "a"
    assert sl.loads('"a"', extension="yml") == "a"
    assert sl.loads('"a"', extension="yaml") == "a"

    # 指定した形式でダンプできること
    assert sl.dumps('"a"', extension="null") == '"a"'
    assert sl.dumps("a", extension="json") == '"a"'
    assert sl.dumps("a", extension="yml") == "a\n...\n"
    assert sl.dumps("a", extension="yaml") == "a\n...\n"

    with pytest.raises(NotImplementedError):
        sl.loads("a", extension="no_exists")

    with pytest.raises(NotImplementedError):
        sl.loads("a", extension="")
