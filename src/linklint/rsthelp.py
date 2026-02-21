"""Utilities for RST files."""

import os
import re
import string
import tempfile
from pathlib import Path

from docutils import nodes
from sphinx.application import Sphinx

from linklint import dump


def test_slug() -> str:
    test_name = os.getenv("PYTEST_CURRENT_TEST", "unknown")
    m = re.fullmatch(r"(?P<file>.*)::(?P<test>.*)(?P<param>\[[-._+/\w]+\])(?: \(\w+\))", test_name)
    assert m is not None
    if param := m["param"]:
        return param.strip("[]")
    return m["test"]


def parse_rst_file(content: str) -> nodes.document:
    """Parse an RST file using Sphinx and return the doctree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        outdir = tmppath / "_build"
        doctreedir = outdir / ".doctrees"

        # Create minimal conf.py
        (tmppath / "conf.py").write_text("extensions = []\n")

        # Copy the RST file as index.rst
        (tmppath / "index.rst").write_text(content)

        app = Sphinx(
            srcdir=str(tmppath),
            confdir=str(tmppath),
            outdir=str(outdir),
            doctreedir=str(doctreedir),
            buildername="dummy",
            freshenv=True,
            status=None,
            warning=None,
        )

        app.build()
        doctree = app.env.get_doctree("index")
        fix_node_lines(doctree)

        if os.getenv("DUMP_DOCTREE"):
            os.makedirs("tmp/dump", exist_ok=True)
            with open(f"tmp/dump/{test_slug()}.txt", "w", encoding="utf-8") as f:
                dump.dump_doctree(doctree, f)

        return doctree


BLOCK_NODES = (nodes.paragraph,)


def fix_node_lines(doctree: nodes.document) -> None:
    """Fix line numbers for inline nodes within block elements.

    Doctree block nodes have correct line numbers, but their inline children
    inherit the block's start line.  Walk each block's descendants counting
    newlines in text nodes to compute each inline node's actual line.
    """
    for block in doctree.findall(lambda n: isinstance(n, BLOCK_NODES)):
        if not block.line:
            continue
        newline_count = 0
        for node in block.findall():
            if node is block:
                continue
            node.line = block.line + newline_count
            if isinstance(node, nodes.Text):
                newline_count += str(node).count("\n")


def is_header_line(line: str, text_line: str) -> bool:
    """Check if a line is a header underline/overline for `text_line`."""
    stripped = line.rstrip()
    return len(stripped) >= len(text_line.rstrip()) and len(set(stripped)) == 1 and stripped[0] in string.punctuation


def replace_rst_line(lines: list[str], line_num: int, new_line: str) -> None:
    """Replace a line in the content lines, adjusting header lengths if needed."""
    old_line = lines[line_num]
    lines[line_num] = new_line
    # Adjust adjacent lines if they are header lines.
    for adj_line_num in [line_num - 1, line_num + 1]:
        if adj_line_num in range(len(lines)):
            adj_line = lines[adj_line_num]
            if is_header_line(adj_line, old_line):
                lines[adj_line_num] = adj_line[0] * len(new_line.rstrip()) + adj_line[-1]


def resub_in_rst_line(lines: list[str], line_num: int, pat: str, repl: str, count=0) -> bool:
    """Replace a substring in a line, adjusting header lengths if needed."""
    new_line = re.sub(pat, repl, lines[line_num], count=count)
    changed = new_line != lines[line_num]
    if changed:
        replace_rst_line(lines, line_num, new_line)
    return changed
