def version():
    from importlib.metadata import version

    assert __package__ == "rctl"
    return version(__package__)
