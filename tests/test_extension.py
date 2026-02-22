import os
from pathlib import Path
from typing import Iterable

import pytest

from linklint.rsthelp import run_sphinx
from linklint.utils import in_tempdir

from summarize_html import summarize_html_file


def summarizable_rst_files() -> Iterable[tuple[str, str]]:
    data_files = set(os.listdir("tests/data"))
    for df in data_files:
        if df.endswith(".rst"):
            summary = df.removesuffix(".rst") + "_summary.html"
            if summary in data_files:
                yield (df, summary)


@pytest.mark.parametrize("rst_file, summary_file", summarizable_rst_files())
def test_summarize_html(rst_file: str, summary_file: str) -> None:
    rst = Path("tests/data", rst_file).read_text()
    with in_tempdir():
        run_sphinx(rst, buildername="html", extensions=["linklint.ext"])
        summary = summarize_html_file("_build/index.html")
    expected = Path("tests/data", summary_file).read_text()
    assert summary == expected
