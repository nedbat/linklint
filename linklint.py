"""Linter to find link problems in RST files."""

# Run with:
#   uv run linklint.py **/*.rst

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "Sphinx",
# ]
# ///

import argparse
import re
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.addnodes import pending_xref


@dataclass
class LintIssue:
    line: int
    message: str
    fixed: bool = False


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
        return app.env.get_doctree("index")


@dataclass
class LintWork:
    doctree: nodes.document
    content_lines: list[str]
    fix: bool
    fixed: bool


def replace_rst_line(lines: list[str], line_num: int, new_line: str) -> None:
    """Replace a line in the content lines, adjusting underline lengths if needed."""
    old_line = lines[line_num - 1]
    lines[line_num - 1] = new_line
    # Adjust underline if the next line is an underline of the same length
    if line_num < len(lines):
        next_line = lines[line_num]
        if len(next_line) == len(old_line) and len(set(next_line.rstrip())) == 1:
            lines[line_num] = next_line[0] * len(new_line.rstrip()) + next_line[-1]


def resub_in_rst_line(lines: list[str], line_num: int, pat: str, repl: str) -> None:
    """Replace a substring in a line, adjusting underline lengths if needed."""
    old_line = lines[line_num - 1]
    new_line = re.sub(pat, repl, old_line)
    replace_rst_line(lines, line_num, new_line)


def find_pattern_lines(lines: list[str], pattern: str) -> list[int]:
    """Return 1-based line numbers of lines matching pattern."""
    return [i + 1 for i, line in enumerate(lines) if re.search(pattern, line)]


def find_self_links(work: LintWork) -> Iterable[LintIssue]:
    """Find :mod: references that link to modules declared in the same section."""
    for section in work.doctree.findall(nodes.section):
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

        # Pre-scan for actual line numbers of each target
        target_lines: dict[str, list[int]] = {}
        for ref in section.findall(pending_xref):
            if ref.get("reftype") == "mod":
                target = ref.get("reftarget")
                if target in declared_modules and target not in target_lines:
                    pat = rf":mod:`~?{re.escape(target)}`"
                    target_lines[target] = find_pattern_lines(
                        work.content_lines, pat
                    )

        for ref in section.findall(pending_xref):
            if ref.get("reftype") == "mod":
                target = ref.get("reftarget")
                if target in declared_modules:
                    lines_list = target_lines[target]
                    actual_line = lines_list.pop(0) if lines_list else ref.line
                    fixed = False
                    if work.fix:
                        resub_in_rst_line(
                            work.content_lines,
                            actual_line,
                            rf":mod:`{re.escape(target)}`",
                            rf":mod:`!{target}`",
                        )
                        work.fixed = fixed = True
                    yield LintIssue(
                        actual_line,
                        f"self-link to module '{target}'",
                        fixed=fixed,
                    )


def find_duplicate_refs_in_paragraph(work: LintWork) -> Iterable[LintIssue]:
    """Find references that appear more than once in the same paragraph."""
    for para in work.doctree.findall(nodes.paragraph):
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


def lint_file(filepath: str, fix: bool) -> list[LintIssue]:
    """Lint a single RST file.

    Returns a list of LintIssue objects.
    """
    path = Path(filepath)
    content = path.read_text()
    result = lint_content(content, fix)
    if fix and result.fixed:
        path.write_text(result.content)
    return result.issues


@dataclass
class LintResult:
    content: str
    issues: list[LintIssue]
    fixed: bool


def lint_content(content: str, fix: bool) -> LintResult:
    doctree = parse_rst_file(content)
    work = LintWork(
        content_lines=content.splitlines(keepends=True),
        doctree=doctree,
        fix=fix,
        fixed=False,
    )

    issues = []
    issues.extend(find_self_links(work))
    # issues.extend(find_duplicate_refs_in_paragraph(work))

    result = LintResult(
        content="".join(work.content_lines),
        issues=issues,
        fixed=work.fixed,
    )

    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", help="Fix the issues in place", action="store_true")
    parser.add_argument("files", nargs="+", help="RST files to lint")
    args = parser.parse_args(argv)

    exit_code = 0
    for filepath in args.files:
        # This runs Sphinx on each file separately, which seems slow, but is
        # faster than running it once on all the files.
        for issue in lint_file(filepath, args.fix):
            fixed_suffix = " (fixed)" if issue.fixed else ""
            print(f"{filepath}:{issue.line}: {issue.message}{fixed_suffix}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
