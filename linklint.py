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
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docutils import nodes
from sphinx.addnodes import pending_xref

from rsthelp import parse_rst_file, resub_in_rst_line


@dataclass
class LintIssue:
    line: int
    message: str
    fixed: bool = False


@dataclass
class LintWork:
    doctree: nodes.document
    content_lines: list[str]
    fix: bool
    fixed: bool


CHECKS = {}


def check(name: str):
    """Decorator to register a lint check function."""

    def decorator(func):
        CHECKS[name] = func
        return func

    return decorator


@check("self")
def find_self_modules(work: LintWork) -> Iterable[LintIssue]:
    """Find :mod: references that link to modules declared in the same section."""
    return find_self_links(work, "module", "mod")


@check("selfclass")
def find_self_classes(work: LintWork) -> Iterable[LintIssue]:
    """Find :mod: references that link to classes declared in the same section."""
    return find_self_links(work, "class", "class")


def find_self_links(work: LintWork, long: str, short: str) -> Iterable[LintIssue]:
    """Find references that link to their own section."""
    for section in work.doctree.findall(nodes.section):
        declared_sections = set()
        section_names = set(section.get("names", []))
        for section_id in section.get("ids", []):
            # Explicit targets like `.. _module-foo:` appear in both ids
            # and names; actual `.. module::` directives only appear in ids.
            if section_id.startswith(f"{long}-") and section_id not in section_names:
                name = section_id[len(long) + 1 :]
                declared_sections.add(name)

        if not declared_sections:
            continue

        for ref in section.findall(pending_xref):
            if ref.line is None:
                continue
            if ref.get("reftype") == short:
                target = ref.get("reftarget")
                if target in declared_sections:
                    fixed = False
                    if work.fix:
                        work.fixed = fixed = resub_in_rst_line(
                            lines=work.content_lines,
                            line_num=ref.line - 1,
                            pat=rf":{short}:`[~.]?{re.escape(target)}`",
                            repl=rf":{short}:`!{ref.astext()}`",
                        )
                        if not fixed:
                            print(
                                f"Line {ref.line}: tried",
                                repr(rf":{short}:`[~.]?{re.escape(target)}`"),
                                "to",
                                repr(rf":{short}:`!{ref.astext()}`"),
                            )
                            print(f"Line was: {repr(work.content_lines[ref.line - 1])}")
                    yield LintIssue(
                        ref.line,
                        f"self-link to {long} '{target}'",
                        fixed=fixed,
                    )


@check("paradup")
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


@dataclass
class LintResult:
    content: str
    issues: list[LintIssue]
    fixed: bool


def lint_content(content: str, fix: bool, checks: set[str]) -> LintResult:
    doctree = parse_rst_file(content)
    work = LintWork(
        content_lines=content.splitlines(keepends=True),
        doctree=doctree,
        fix=fix,
        fixed=False,
    )

    issues = []
    for check_name in checks:
        issues.extend(CHECKS[check_name](work))

    result = LintResult(
        content="".join(work.content_lines),
        issues=issues,
        fixed=work.fixed,
    )

    return result


def lint_file(filepath: str, fix: bool, checks: set[str]) -> list[LintIssue]:
    """Lint a single RST file.

    Returns a list of LintIssue objects.
    """
    path = Path(filepath)
    content = path.read_text()
    result = lint_content(content, fix, checks)
    if fix and result.fixed:
        path.write_text(result.content)
    return result.issues


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        help=f"comma-separated checks to run ({', '.join(CHECKS)}, all)",
        default="all",
    )
    parser.add_argument("--fix", help="Fix the issues in place", action="store_true")
    parser.add_argument("files", nargs="+", help="RST files to lint")
    args = parser.parse_args(argv)

    checks = set(args.check.split(","))
    unknown = checks - set(CHECKS.keys()) - {"all"}
    if unknown:
        print(f"Unknown checks: {', '.join(unknown)}", file=sys.stderr)
        return 2
    if "all" in checks:
        checks = set(CHECKS.keys())

    issues = 0
    for filepath in args.files:
        # This runs Sphinx on each file separately, which seems slow, but is
        # faster than running it once on all the files.
        for issue in lint_file(filepath, args.fix, checks):
            fixed_suffix = " (fixed)" if issue.fixed else ""
            print(f"{filepath}:{issue.line}: {issue.message}{fixed_suffix}")
            issues += 1

    print(f"Checked {len(args.files)} file(s), found {issues} issue(s).")
    return issues > 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
