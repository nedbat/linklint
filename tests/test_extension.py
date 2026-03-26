"""
Tests using .toml files in tests/data.

Sphinx renders the rst to HTML, then we compare a summary of the HTML to the
expected html from the .toml file.

"""

import shutil
from pathlib import Path

import pytest

from linklint.rsthelp import run_sphinx, save_test_doctree
from linklint.utils import SAVE_INTERMEDIATE, in_tempdir

from helpers import DATA_DIR, read_toml
from summarize_html import summarize_html_file


PROJECT = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "toml_name",
    [p.stem for p in sorted(DATA_DIR.glob("*.toml"))],
)
def test_summarize_html(toml_name: str) -> None:
    data = read_toml(toml_name)
    rst = data["rst"]
    with in_tempdir():
        result = run_sphinx(rst, buildername="html", extensions=["linklint.ext"])
        summary = summarize_html_file("_build/index.html")
        if SAVE_INTERMEDIATE:
            # In case of needing to see what happened, copy the HTML etc to tmp.
            shutil.copytree("_build/_static", PROJECT / "tmp/html/_static", dirs_exist_ok=True)
            shutil.copyfile("_build/index.html", PROJECT / f"tmp/html/{toml_name}.html")
            (PROJECT / f"tmp/html/{toml_name}_summary.html").write_text(summary, encoding="utf-8")

            # Also run without the extension to understand Sphinx native behavior.
            run_sphinx(rst, buildername="html", extensions=[])
            shutil.copyfile("_build/index.html", PROJECT / f"tmp/html/{toml_name}_nofix.html")
            nofix_summary = summarize_html_file("_build/index.html")
            (PROJECT / f"tmp/html/{toml_name}_summary_nofix.html").write_text(
                nofix_summary, encoding="utf-8"
            )
            save_test_doctree(result.doctree)

    # Check the expected HTML output.
    assert 'class="self-link"' not in summary, f"Self-links found in {toml_name}"
    expected = data["html"]

    if summary != expected:  # pragma: only failure
        if SAVE_INTERMEDIATE:
            print(f"Full HTML is at tmp/html/{toml_name}.html")
            print(f"Summary is at tmp/html/{toml_name}_summary.html")
            print(f"Update {toml_name} with the correct output")
        else:
            print("To see full HTML, set LINKLINT_SAVE_INTERMEDIATE=1 and re-run the test.")

    assert summary == expected

    # Check the expected status message output.
    output = "".join(ln for ln in result.status.splitlines(keepends=True) if "Linklint" in ln)
    assert output == data["output"]
