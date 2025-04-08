from rctl.core import (
    absent_resource,
    apply_resource,
    create_resource,
    delete_resource,
    exists_resource,
    recreate_resource,
    scan_resource,
)

from .core import AppTyper

app = AppTyper()


app.command("apply")(apply_resource)
app.command("create")(create_resource)
app.command("exists")(exists_resource)
app.command("absent")(absent_resource)
app.command("delete")(delete_resource)
app.command("recreate")(recreate_resource)
app.command("scan")(scan_resource)
