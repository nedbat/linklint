from typing import cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata

import linklint
from linklint.linklint import find_self_refs


def process_reference_nodes(app, doctree):
    for ref in find_self_refs(doctree):
        cast(nodes.Element, ref.parent).replace(ref, ref.children[0])


def setup(app: Sphinx) -> ExtensionMetadata:
    app.connect("doctree-read", process_reference_nodes)

    return {
        "version": linklint.__version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
