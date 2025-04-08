import functools

from lark import Lark

from .files import PARSER_FILE


@functools.lru_cache()
def parser() -> Lark:
    """Build standard parser for transforming HCL2 text into python structures"""
    return Lark.open(
        "grammar.lark",
        parser="lalr",
        cache=str(PARSER_FILE),  # Disable/Delete file to effect changes to the grammar
        rel_to=__file__,
        propagate_positions=True,
        start="start",
    )
