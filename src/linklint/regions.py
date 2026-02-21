from dataclasses import dataclass
from typing import Iterable

from docutils import nodes
from sphinx import addnodes


@dataclass
class Region:
    # "module", "class", "function", etc.
    kind: str
    name: str
    # Line number where the region starts.
    start: int
    # Line number where the main part of the region ends: the lines in this
    # region and not in any nested subregion.
    end_main: int
    # Line number where the whole region ends: includes all nested subregions.
    end_total: int

    def __lt__(self, other):
        return (self.start, self.name) < (other.start, other.name)


class RegionFinder:
    def __init__(self) -> None:
        self.last_line = 0

    def find_regions(self, node: nodes.Node) -> Iterable[Region]:
        kind = None
        end_main = None

        match node:
            case nodes.section():
                section_names = set(node.get("names", []))
                for section_id in node.get("ids", []):
                    if section_id.startswith("module-") and section_id not in section_names:
                        kind = "module"
                        name = section_id[len("module-") :]
                        assert node.line is not None
                        start = node.line - 1
                        break

            case addnodes.desc():
                kind = node.get("objtype")
                child0 = node.children[0]
                name = child0.get("fullname")
                start = child0.line

        last_line = getattr(node, "line", None)
        if last_line is not None:
            self.last_line = last_line + node.astext().count("\n")

        for child in node.children:
            for subregion in self.find_regions(child):
                if kind is not None and end_main is None:
                    # The main part of a region ends when the next region starts.
                    end_main = subregion.start - 1
                yield subregion

        if kind is not None:
            yield Region(
                kind=kind,
                name=name,
                start=start,
                end_main=end_main or self.last_line,
                end_total=self.last_line,
            )


def find_regions(doctree: nodes.document) -> Iterable[Region]:
    """Find regions in the doctree."""
    finder = RegionFinder()
    return finder.find_regions(doctree)
