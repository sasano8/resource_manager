import typer


def main():
    from .cli import resource

    app = typer.Typer(no_args_is_help=True)
    app.add_typer(resource.app, name="resource")
    app()


if __name__ == "__main__":
    main()
