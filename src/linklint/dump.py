import sys
from typing import TextIO

from docutils import nodes


INTERESTING_KEYS = [
    "ids",
    "names",
    "reftype",
    "reftarget",
    "refuri",
    "domain",
    "objtype",
    "desctype",
    "class",
    "fullname",
    "module",
]

INTERESTING_ATTRS = [
    # "rawsource",
]


def dump_doctree(node: nodes.Node, fp: TextIO, indent: int = 0) -> None:
    """Print a nicely formatted tree of a docutils doctree."""
    prefix = "    " * indent
    if isinstance(node, nodes.Text):
        text = node.astext()
        print(f"{prefix}Text: {text!r}", file=fp)
    else:
        tag = node.__class__.__name__
        attrs = []
        for key in INTERESTING_KEYS:
            if val := node.get(key):  # type: ignore
                attrs.append(f"{key}={val!r}")
        for attr in INTERESTING_ATTRS:
            if val := getattr(node, attr, None):
                attrs.append(f".{attr}={val!r}")
        attr_str = f" {{{', '.join(attrs)}}}" if attrs else ""
        if tag == "reference":
            print(vars(node), file=fp)
        line = node.line
        line_str = f" @{line}" if line else ""
        print(f"{prefix}{tag}{attr_str}{line_str}", file=fp)
        # print(f"{prefix}{node.attributes}", file=fp)
        for child in node.children:
            dump_doctree(child, fp, indent + 1)


if __name__ == "__main__":
    from linklint.linklint import parse_rst_file

    with open(sys.argv[1]) as f:
        dump_doctree(parse_rst_file(f.read()), sys.stdout)
