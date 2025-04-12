from fsspec.gui import FileSelector

panel_app = FileSelector(
    url="array://.", kwargs={"filesystems": {"b": {"protocol": "local"}}}
)
panel_app.show()
