from typing import cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util import logging
from sphinx.util.typing import ExtensionMetadata

import linklint
from linklint.linklint import find_duplicate_refs, find_self_refs

logger = logging.getLogger(__name__)


def init_data(app: Sphinx) -> None:
    app.env.linklint_count: int = 0


def process_reference_nodes(app, doctree):
    """Find references that shouldn't be links, and un-reference them."""
    # Change <reference><literal></reference> to just <literal>.

    for finder in (find_self_refs, find_duplicate_refs):
        for ref in finder(doctree):
            cast(nodes.Element, ref.parent).replace(ref, ref.children[0])
            app.env.linklint_count += 1


def merge_data(
    app: Sphinx,
    env: BuildEnvironment,
    docnames: list[str],
    other: BuildEnvironment,
) -> None:
    env.linklint_count += other.linklint_count  # type: ignore


def display_results(app: Sphinx, exception: Exception | None) -> None:
    if not exception:
        assert hasattr(app.env, "linklint_count")
        logger.info(f"Linklint unlinked {app.env.linklint_count} references.")


def setup(app: Sphinx) -> ExtensionMetadata:
    app.connect("builder-inited", init_data)
    app.connect("doctree-read", process_reference_nodes)
    app.connect("env-merge-info", merge_data)
    app.connect("build-finished", display_results)

    return {
        "version": linklint.__version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
