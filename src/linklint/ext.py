from typing import cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata

import linklint
from linklint.linklint import find_duplicate_refs, find_self_refs


def process_reference_nodes(app, doctree):
    """Find references that shouldn't be links, and un-reference them."""
    # Change <reference><literal></reference> to just <literal>.

    for finder in (find_self_refs, find_duplicate_refs):
        for ref in finder(doctree):
            cast(nodes.Element, ref.parent).replace(ref, ref.children[0])


def setup(app: Sphinx) -> ExtensionMetadata:
    app.connect("doctree-read", process_reference_nodes)

    return {
        "version": linklint.__version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
