"""Utilities for RST files."""

import re
import string
import tempfile
from pathlib import Path

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx


def on_doctree_read(app, doctree):
    for node in doctree.findall(addnodes.desc):
        if node.get("domain") == "py":
            sig = node.children[0]  # desc_signature
            ntype = node.get("objtype")
            while node is not None:
                if isinstance(node, nodes.section):
                    node.get('ids').append(f"{ntype}-{sig.get('fullname')}")
                    break
                node = node.parent


def setup(app):
    app.connect("doctree-read", on_doctree_read)


def parse_rst_file(content: str) -> nodes.document:
    """Parse an RST file using Sphinx and return the doctree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        outdir = tmppath / "_build"
        doctreedir = outdir / ".doctrees"

        # Create minimal conf.py
        (tmppath / "conf.py").write_text("extensions = ['rsthelp']\n")

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
        return doctree


BLOCK_NODES = (nodes.paragraph,)


def fix_node_lines(doctree: nodes.document) -> None:
    """Fix line numbers for inline nodes within block elements.

    Doctree block nodes (paragraphs, titles) have correct line numbers, but
    their inline children all inherit the block's start line.  Walk each block's
    descendants counting newlines in text nodes to compute each inline node's
    actual line.
    """
    for block in doctree.findall(lambda n: isinstance(n, BLOCK_NODES)):
        if not block.line:
            continue
        newline_count = 0
        for node in block.findall():
            if node is block:
                continue
            if isinstance(node, nodes.Text):
                newline_count += str(node).count("\n")
            else:
                node.line = block.line + newline_count


def is_header_line(line: str, text_line: str) -> bool:
    """Check if a line is a header underline/overline for `text_line`."""
    stripped = line.rstrip()
    return (
        len(stripped) >= len(text_line.rstrip())
        and len(set(stripped)) == 1
        and stripped[0] in string.punctuation
    )


def replace_rst_line(lines: list[str], line_num: int, new_line: str) -> None:
    """Replace a line in the content lines, adjusting header lengths if needed."""
    old_line = lines[line_num]
    lines[line_num] = new_line
    # Adjust adjacent lines if they are header lines.
    for adj_line_num in [line_num - 1, line_num + 1]:
        if adj_line_num in range(len(lines)):
            adj_line = lines[adj_line_num]
            if is_header_line(adj_line, old_line):
                lines[adj_line_num] = (
                    adj_line[0] * len(new_line.rstrip()) + adj_line[-1]
                )


def resub_in_rst_line(lines: list[str], line_num: int, pat: str, repl: str, count=0) -> bool:
    """Replace a substring in a line, adjusting header lengths if needed."""
    new_line = re.sub(pat, repl, lines[line_num], count=count)
    changed = new_line != lines[line_num]
    if changed:
        replace_rst_line(lines, line_num, new_line)
    return changed
