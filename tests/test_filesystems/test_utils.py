def test_normalize():
    from rctl2.filesystems.utils import normalize_path

    assert normalize_path("a") == "a"
    assert normalize_path("/") == ""
    assert normalize_path("/a") == "a"
    assert normalize_path("a/") == "a"
    assert normalize_path("/a/") == "a"
    assert normalize_path("") == ""
    assert normalize_path(".") == ""
    assert normalize_path("data.json") == "data.json"
    assert normalize_path("data.") == "data."
    assert normalize_path(".data") == ".data"
    assert normalize_path(".data.") == ".data."

    assert normalize_path("/a//b///c////d/////") == "a/b/c/d"
    assert normalize_path("./a//.///b////.") == "a/b"
