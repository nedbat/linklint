"""Linter to find self-referential links in RST files."""

import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.addnodes import pending_xref


@dataclass
class LintIssue:
    line: int
    message: str


def parse_rst_file(filepath: Path) -> nodes.document:
    """Parse an RST file using Sphinx and return the doctree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        outdir = tmppath / "_build"
        doctreedir = outdir / ".doctrees"

        # Create minimal conf.py
        (tmppath / "conf.py").write_text("extensions = []\n")

        # Copy the RST file as index.rst
        content = filepath.read_text()
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
        return app.env.get_doctree("index")


def find_self_links(doctree: nodes.document):
    """Find :mod: references that link to modules declared in the same section."""
    for section in doctree.findall(nodes.section):
        declared_modules = set()
        section_names = set(section.get("names", []))
        for section_id in section.get("ids", []):
            # Explicit targets like `.. _module-foo:` appear in both ids
            # and names; actual `.. module::` directives only appear in ids.
            if section_id.startswith("module-") and section_id not in section_names:
                module_name = section_id[7:]
                declared_modules.add(module_name)

        if not declared_modules:
            continue

        for ref in section.findall(pending_xref):
            if ref.get("reftype") == "mod":
                target = ref.get("reftarget")
                if target in declared_modules:
                    yield LintIssue(ref.line, f"self-link to module '{target}'")


def find_duplicate_refs_in_paragraph(doctree: nodes.document):
    """Find references that appear more than once in the same paragraph."""
    for para in doctree.findall(nodes.paragraph):
        refs_by_target = defaultdict(list)
        for ref in para.findall(pending_xref):
            reftype = ref.get("reftype")
            target = ref.get("reftarget")
            if reftype and target:
                refs_by_target[(reftype, target)].append(ref)

        for (reftype, target), refs in refs_by_target.items():
            if len(refs) > 1:
                for ref in refs[1:]:
                    yield LintIssue(
                        ref.line,
                        f"duplicate :{reftype}:`{target}` in paragraph",
                    )


def lint_file(filepath: Path) -> list[LintIssue]:
    """Lint a single RST file.

    Returns a list of LintIssue objects.
    """
    doctree = parse_rst_file(filepath)
    issues = []
    issues.extend(find_self_links(doctree))
    #issues.extend(find_duplicate_refs_in_paragraph(doctree))
    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: linklint.py <file.rst> [file2.rst ...]", file=sys.stderr)
        sys.exit(1)

    exit_code = 0
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        # This runs Sphinx on each file separately, which seems slow, but is
        # faster than running it once on all the files.
        issues = lint_file(path)
        for issue in issues:
            print(f"{filepath}:{issue.line}: {issue.message}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
