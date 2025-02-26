import typer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    AppTyper = typer.Typer
else:

    class AppTyper(typer.Typer):
        def __init__(self, no_args_is_help=True, **kwargs):
            super().__init__(no_args_is_help=no_args_is_help, **kwargs)

        def command(self, name=None, no_args_is_help: bool = True, **kwargs):
            return super().command(name, no_args_is_help=no_args_is_help, **kwargs)
