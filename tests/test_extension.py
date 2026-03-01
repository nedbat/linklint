"""
Tests using .rst files in tests/data.

Sphinx renders them to HTML, then we compare a summary of the HTML to an
expected summary in a corresponding .html file.

"""

import shutil
from pathlib import Path

import pytest

from linklint.rsthelp import run_sphinx, save_test_doctree
from linklint.utils import SAVE_INTERMEDIATE, in_tempdir

from summarize_html import summarize_html_file


PROJECT = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "rst_file",
    [r.name for r in Path("tests/data").glob("*.rst")],
)
def test_summarize_html(rst_file: str) -> None:
    rst = (PROJECT / "tests/data" / rst_file).read_text()
    root = rst_file.removesuffix(".rst")
    with in_tempdir():
        doctree = run_sphinx(rst, buildername="html", extensions=["linklint.ext"])
        summary = summarize_html_file("_build/index.html")
        if SAVE_INTERMEDIATE:
            # In case of needing to see what happened, copy the HTML etc to tmp.
            shutil.copytree("_build/_static", PROJECT / "tmp/html/_static", dirs_exist_ok=True)
            shutil.copyfile("_build/index.html", PROJECT / f"tmp/html/{root}.html")
            (PROJECT / f"tmp/html/{root}_summary.html").write_text(summary)

            # Also run without the extension to understand Sphinx native behavior.
            run_sphinx(rst, buildername="html", extensions=[])
            shutil.copyfile("_build/index.html", PROJECT / f"tmp/html/{root}_nofix.html")
            nofix_summary = summarize_html_file("_build/index.html")
            (PROJECT / f"tmp/html/{root}_summary_nofix.html").write_text(nofix_summary)

    save_test_doctree(doctree)
    assert 'class="self-link"' not in summary, f"Self-links found in {root}.html"
    summary_file = PROJECT / f"tests/data/{root}_summary.html"
    if summary_file.exists():
        expected = summary_file.read_text()
    else:
        expected = f"Summary {summary_file} doesn't exist"  # pragma: only failure

    if summary != expected:  # pragma: only failure
        if SAVE_INTERMEDIATE:
            print(f"Full HTML is at tmp/html/{root}.html")
            print(f"Summary is at tmp/html/{root}_summary.html")
            print("if the full HTML is correct:")
            print(f"  $ cp tmp/html/{root}_summary.html tests/data/{root}_summary.html")
        else:
            print("To see full HTML, set LINKLINT_SAVE_INTERMEDIATE=1 and re-run the test.")

    assert summary == expected
