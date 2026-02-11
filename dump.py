import sys

from linklint import *


def dump_doctree(node: nodes.Node, indent: int = 0) -> None:
    """Print a nicely formatted tree of a docutils doctree."""
    prefix = "  " * indent
    if isinstance(node, nodes.Text):
        text = node.astext()
        # if len(text) > 60:
        #     text = text[:57] + "..."
        print(f"{prefix}Text: {text!r}")
    else:
        tag = node.__class__.__name__
        attrs = {}
        for key in ("ids", "names", "reftype", "reftarget", "refuri"):
            val = node.get(key)
            if val:
                attrs[key] = val
        attr_str = f" {attrs}" if attrs else ""
        line = node.get("line") or getattr(node, "line", None)
        line_str = f" L{line}" if line else ""
        print(f"{prefix}{tag}{attr_str}{line_str}")
        for child in node.children:
            dump_doctree(child, indent + 1)


with open(sys.argv[1]) as f:
    tree = parse_rst_file(f.read())

dump_doctree(tree)
