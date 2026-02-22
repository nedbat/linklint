import os
from pathlib import Path
from typing import Iterable

import pytest

from linklint.rsthelp import run_sphinx
from linklint.utils import in_tempdir

from summarize_html import summarize_html_file


def summarizable_rst_files() -> Iterable[str]:
    data_files = set(os.listdir("tests/data"))
    for df in data_files:
        if df.endswith(".rst"):
            root = df.removesuffix(".rst")
            summary = root + "_summary.html"
            if summary in data_files:
                yield root


@pytest.mark.parametrize("root", summarizable_rst_files())
def test_summarize_html(root: str) -> None:
    rst = Path("tests/data", f"{root}.rst").read_text()
    with in_tempdir():
        run_sphinx(rst, buildername="html", extensions=["linklint.ext"])
        summary = summarize_html_file("_build/index.html")
    expected = Path("tests/data", f"{root}_summary.html").read_text()
    assert summary == expected
