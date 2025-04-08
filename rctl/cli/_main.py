import typer

from rctl.api import version as _get_version

from . import resource

app = typer.Typer(no_args_is_help=True)
app.add_typer(resource.app, name="resource")


@app.command(no_args_is_help=False)
def version():
    v = _get_version()
    print(v)
