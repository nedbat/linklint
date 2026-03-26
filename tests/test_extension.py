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
    Path("tests/data").glob("*.rst"),
    ids=lambda p: p.stem,
)
def test_summarize_html(rst_file: Path) -> None:
    rst = rst_file.read_text(encoding="utf-8")
    root = rst_file.stem
    with in_tempdir():
        result = run_sphinx(rst, buildername="html", extensions=["linklint.ext"])
        summary = summarize_html_file("_build/index.html")
        if SAVE_INTERMEDIATE:
            # In case of needing to see what happened, copy the HTML etc to tmp.
            shutil.copytree("_build/_static", PROJECT / "tmp/html/_static", dirs_exist_ok=True)
            shutil.copyfile("_build/index.html", PROJECT / f"tmp/html/{root}.html")
            (PROJECT / f"tmp/html/{root}_summary.html").write_text(summary, encoding="utf-8")

            # Also run without the extension to understand Sphinx native behavior.
            run_sphinx(rst, buildername="html", extensions=[])
            shutil.copyfile("_build/index.html", PROJECT / f"tmp/html/{root}_nofix.html")
            nofix_summary = summarize_html_file("_build/index.html")
            (PROJECT / f"tmp/html/{root}_summary_nofix.html").write_text(
                nofix_summary, encoding="utf-8"
            )
            save_test_doctree(result.doctree)

    # Check the expected HTML output.
    assert 'class="self-link"' not in summary, f"Self-links found in {root}.html"
    expected_file = Path(f"tests/data/{root}_summary.html")
    if expected_file.exists():
        expected = expected_file.read_text(encoding="utf-8")
    else:
        expected = f"Expected summary {expected_file} doesn't exist"  # pragma: only failure

    if summary != expected:  # pragma: only failure
        if SAVE_INTERMEDIATE:
            print(f"Full HTML is at tmp/html/{root}.html")
            print(f"Summary is at tmp/html/{root}_summary.html")
            print("if the full HTML is correct:")
            print(f"  $ cp tmp/html/{root}_summary.html tests/data/{root}_summary.html")
        else:
            print("To see full HTML, set LINKLINT_SAVE_INTERMEDIATE=1 and re-run the test.")

    assert summary == expected

    # Check the expected status message output.
    output = "".join(ln for ln in result.status.splitlines(keepends=True) if "Linklint" in ln)
    expected_output_file = Path(f"tests/data/{root}_output.txt")
    if expected_output_file.exists():
        expected_output = expected_output_file.read_text()
    else:
        expected_output = (
            f"Expected output {expected_output_file} doesn't exist"  # pragma: only failure
        )

    assert output == expected_output
