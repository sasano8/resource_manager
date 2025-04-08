import click
import typer

from ..api import RctlWorkSpace
from .core import AppTyper

app = AppTyper()
config = AppTyper()
app.add_typer(config, name="config")


@app.command(no_args_is_help=False)
def version():
    typer.echo("0.0.1")


@config.command(no_args_is_help=False)
def init(app_name: str = None, env_name: str = "default", override: bool = False):
    obj = RctlWorkSpace.config_init(app_name=app_name, env_name=env_name)
    result = obj.config_save(override=override)
    result.dispatch(typer.echo, click.ClickException)


@config.command(no_args_is_help=False)
def show(app_name: str = "*", env_name: str = "*"):
    ok, msg = RctlWorkSpace.config_exists()
    if not ok:
        raise click.ClickException(msg)

    obj = RctlWorkSpace.config_load()
    text = obj.config_show()
    typer.echo(text)
