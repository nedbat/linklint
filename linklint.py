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
import collections
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docutils import nodes
from sphinx import addnodes

from regions import Region, find_regions
from rsthelp import parse_rst_file, resub_in_rst_line


class Resolver:
    # Build a map from reference roles to object types.

    ObjType = lambda _, *refs: refs  # noqa: E731
    _ = lambda s: 0  # noqa: E731

    # object_types map from sphinx
    # sphinx/sphinx/domains/python/__init__.py:725
    object_types = {
        "function": ObjType(_("function"), "func", "obj"),
        "data": ObjType(_("data"), "data", "obj"),
        "class": ObjType(_("class"), "class", "exc", "obj"),
        "exception": ObjType(_("exception"), "exc", "class", "obj"),
        "method": ObjType(_("method"), "meth", "obj"),
        "classmethod": ObjType(_("class method"), "meth", "obj"),
        "staticmethod": ObjType(_("static method"), "meth", "obj"),
        "attribute": ObjType(_("attribute"), "attr", "obj"),
        "property": ObjType(_("property"), "attr", "_prop", "obj"),
        "type": ObjType(_("type alias"), "type", "class", "obj"),
        "module": ObjType(_("module"), "mod", "obj"),
    }

    reftype_to_objtype = collections.defaultdict(list)
    for objtype, names in object_types.items():
        for name in names:
            reftype_to_objtype[name].append(objtype)

    def __init__(self, doctree: nodes.document) -> None:
        self.region_map = {(r.kind, r.name): r for r in find_regions(doctree)}

    def find_region(self, reftype: str, target: str) -> Region | None:
        for objtype in self.reftype_to_objtype[reftype]:
            region = self.region_map.get((objtype, target))
            if region is not None:
                return region
        return None


@dataclass
class LintIssue:
    line: int
    message: str
    fixed: bool = False


@dataclass
class LintWork:
    doctree: nodes.document
    content_lines: list[str]
    resolver: Resolver
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
def find_self_links(work: LintWork) -> Iterable[LintIssue]:
    for ref in work.doctree.findall(addnodes.pending_xref):
        if ref.line is None:
            continue
        reftype = ref.get("reftype")
        target = ref.get("reftarget")
        region = work.resolver.find_region(reftype, target)
        if region is None:
            continue

        start = region.start
        # It might be that we sometimes want end_main, or we want it to be
        # configurable, or something?
        end = region.end_total
        if start <= ref.line <= end:
            fixed = False
            if work.fix:
                pat = rf":{reftype}:`[~.]?{re.escape(target)}`"
                repl = rf":{reftype}:`!{target}`"
                work.fixed = fixed = resub_in_rst_line(
                    lines=work.content_lines,
                    line_num=ref.line - 1,
                    pat=pat,
                    repl=repl,
                    count=1,
                )
                if not fixed:
                    print(f"Line {ref.line}: tried {pat!r} to {repl!r}")
                    print(f"Line was: {work.content_lines[ref.line - 1]!r}")
            yield LintIssue(
                ref.line,
                f"self-link to {region.kind} '{target}'",
                fixed=fixed,
            )


@check("paradup")
def find_duplicate_refs_in_paragraph(work: LintWork) -> Iterable[LintIssue]:
    """Find references that appear more than once in the same paragraph."""
    for para in work.doctree.findall(nodes.paragraph):
        refs_by_target = defaultdict(list)
        for ref in para.findall(addnodes.pending_xref):
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
        resolver=Resolver(doctree),
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
    #print(filepath)
    path = Path(filepath)
    content = path.read_text()
    result = lint_content(content, fix, checks)
    if fix and result.fixed:
        path.write_text(result.content)
    return result.issues


def plural(n: int, thing: str = "", things: str = "") -> str:
    """Pluralize a word.

    If n is 1, return thing.  Otherwise return things, or thing+s.
    """
    if n == 1:
        noun = thing
    else:
        noun = things or (thing + "s")
    return f"{n} {noun}"


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
    fixed = 0
    for filepath in args.files:
        # This runs Sphinx on each file separately, which seems slow, but is
        # faster than running it once on all the files.
        for issue in lint_file(filepath, args.fix, checks):
            fixed_suffix = ""
            if issue.fixed:
                fixed_suffix = " (fixed)"
                fixed += 1
            print(f"{filepath}:{issue.line}: {issue.message}{fixed_suffix}")
            issues += 1

    summary = f"Checked {plural(len(args.files), 'file')}, found {plural(issues, 'issue')}"
    if args.fix:
        summary += f", fixed {fixed}"
    print(f"{summary}.")

    return issues > 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
