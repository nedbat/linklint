import contextlib
import os
import re
import tempfile
from typing import cast

from docutils import nodes


def slug_for_test() -> str:
    """Get the short name of the current test, possibly the param id."""
    test_name = os.getenv("PYTEST_CURRENT_TEST", "unknown")
    m = re.search(r"::(?P<test>[\w_]+)(?P<param>\[.+?\])?(?: \(\w+\))$", test_name)
    assert m is not None
    if param := m["param"]:
        return re.sub(r"[^\w]", "-", param.strip("[]"))
    return m["test"]


@contextlib.contextmanager
def in_tempdir():
    """Make a temp directory and cd into it, then come back and delete it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with contextlib.chdir(tmpdir):
            yield


def plural(n: int, thing: str = "", things: str = "") -> str:
    """Pluralize a word.

    If n is 1, return thing.  Otherwise return things, or thing+s.
    """
    if n == 1:
        noun = thing
    else:
        noun = things or (thing + "s")
    return f"{n} {noun}"


def node_line_number(node: nodes.Node) -> int:
    """Find a line number for a node, looking at parents if needed."""
    while node.line is None:
        node = cast(nodes.Node, node.parent)
    return node.line


def node_traceback(node: nodes.Node) -> str:
    """Get a multi-line traceback for a node to pinpoint problems."""
    lines = []
    while node is not None:
        lineno = str(node.line) if node.line is not None else ""
        lines.append(f"{lineno:>4}: {node!r}")
        node = cast(nodes.Node, node.parent)
    return "\n".join(reversed(lines))
