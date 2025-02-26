from .core import AppTyper
from rctl.core import (
    apply_resource,
    create_resource,
    exists_resource,
    absent_resource,
    recreate_resource,
    delete_resource,
)

app = AppTyper()


app.command("apply")(apply_resource)
app.command("create")(create_resource)
app.command("exists")(exists_resource)
app.command("absent")(absent_resource)
app.command("delete")(delete_resource)
app.command("recreate")(recreate_resource)
