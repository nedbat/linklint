import argparse
import sys
from pathlib import Path

from linklint.linklint import CHECKS, LintIssue, lint_content
from linklint.utils import plural


def lint_file(filepath: str, fix: bool, checks: set[str]) -> list[LintIssue]:
    """Lint a single RST file.

    Returns a list of LintIssue objects.
    """
    # print(filepath)
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")
    result = lint_content(content, fix, checks)
    if fix and result.fixed:
        path.write_text(result.content, encoding="utf-8")
    return result.issues


def linklint(argv: list[str]) -> int:
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


def main():
    sys.exit(linklint(sys.argv[1:]))
