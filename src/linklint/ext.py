from collections import Counter
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
    # Map from docname to {label: count}
    app.env.linklint_counts: dict[str, dict[str, int]] = {}


FINDERS = [
    (find_self_refs, "self"),
    (find_duplicate_refs, "duplicate"),
]


def process_reference_nodes(app, doctree):
    """Find references that shouldn't be links, and un-reference them."""
    # Change <reference><literal></reference> to just <literal>.

    counts = Counter()
    for finder, label in FINDERS:
        for ref in finder(doctree):
            cast(nodes.Element, ref.parent).replace(ref, ref.children[0])
            counts[label] += 1
    app.env.linklint_counts[app.env.docname] = counts


def merge_data(
    app: Sphinx,
    env: BuildEnvironment,
    docnames: list[str],
    other: BuildEnvironment,
) -> None:
    # Env's start as copies of other envs, so we have to be careful to only
    # merge data for the docnames that are actually being merged.
    for docname in docnames:
        if docname in other.linklint_counts:  # type: ignore
            env.linklint_counts[docname] = other.linklint_counts[docname]  # type: ignore


def display_results(app: Sphinx, exception: Exception | None) -> None:
    if not exception:
        totals = Counter()
        for counts in app.env.linklint_counts.values():  # type: ignore
            totals += counts
        total = sum(totals.values())
        details = ", ".join(f"{n} {label}" for label, n in sorted(totals.items()) if n)
        msg = f"Linklint: unlinked {total} refs"
        if details:
            msg += f": {details}"
        logger.info(msg)


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
