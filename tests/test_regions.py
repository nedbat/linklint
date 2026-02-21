from textwrap import dedent
from pathlib import Path

import pytest

from linklint.regions import Region, find_regions
from linklint.rsthelp import parse_rst_file


def RegionTestCase(*, rst: str, regions: list[Region], id:str = ""):
    """Helper to create pytest parameters for tests."""
    if "\n" in rst:
        rst = dedent(rst)
    else:
        # It's a file name
        assert not id
        id = rst
        rst = (Path(__file__).parent / "data" / rst).read_text()
    if not id:
        id = "region"
    return pytest.param(rst, regions, id=id)


TEST_CASES = [
    # The `contents::` directive makes unnumbered paragraphs.
    RegionTestCase(
        id="unnumbered",
        rst="""\
            ======================
            Design and History FAQ
            ======================

            .. only:: html

               .. contents::

            Why does Python use indentation for grouping of statements?
            -----------------------------------------------------------

            Guido van Rossum believes that using indentation for grouping is extremely
            elegant and contributes a lot to the clarity of the average Python program.
            Most people learn to love this feature after a while.
            """,
        regions=[],
    ),
    RegionTestCase(
        id="mymodule",
        rst="""\
                1My Module
                ==========

                .. module:: mymodule

                6This is the :mod:`mymodule` documentation.

                8Also check :mod:`othermodule` for related functionality.
                lorem ipsum quia dolor sit amet consectetur adipisci velit, sed quia non
                numquam eius modi tempora incidunt, ut labore et dolore magnam aliquam quaerat
                voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam
                12corporis suscipit laboriosam.

                14more about this module
                ------------------------

                17lorem ipsum quia dolor sit amet consectetur adipisci velit, sed
                quia non numquam eius modi tempora incidunt.

                20Other Section
                ===============

                23This section references :mod:`mymodule` which is fine.
                """,
        regions=[Region(kind="module", name="mymodule", start=1, end_main=18, end_total=18)],
    ),
    RegionTestCase(
        rst="lzma.rst",
        regions=[
            Region("exception", "LZMAError", start=26, end_main=29, end_total=29),
            Region("function", "open", start=35, end_main=68, end_total=68),
            Region("method", "LZMAFile.peek", start=108, end_main=117, end_total=117),
            Region("attribute", "LZMAFile.mode", start=119, end_main=123, end_total=123),
            Region("attribute", "LZMAFile.name", start=125, end_main=130, end_total=130),
            Region("class", "LZMAFile", start=71, end_main=107, end_total=141),
            Region("method", "LZMACompressor.compress", start=209, end_main=215, end_total=215),
            Region("method", "LZMACompressor.flush", start=217, end_main=222, end_total=222),
            Region("class", "LZMACompressor", start=147, end_main=208, end_total=222),
            Region("method", "LZMADecompressor.decompress", start=254, end_main=279, end_total=279),
            Region("attribute", "LZMADecompressor.check", start=281, end_main=285, end_total=285),
            Region("attribute", "LZMADecompressor.eof", start=287, end_main=289, end_total=289),
            Region("attribute", "LZMADecompressor.unused_data", start=291, end_main=295, end_total=295),
            Region("attribute", "LZMADecompressor.needs_input", start=297, end_main=302, end_total=302),
            Region("class", "LZMADecompressor", start=225, end_main=253, end_total=302),
            Region("function", "compress", start=304, end_main=310, end_total=310),
            Region("function", "decompress", start=313, end_main=322, end_total=322),
            Region("function", "is_check_supported", start=328, end_main=335, end_total=335),
            Region("module", "lzma", start=1, end_main=25, end_total=346),
        ],
    ),
]


@pytest.mark.parametrize("rst, regions", TEST_CASES)
def test_regions(rst, regions):
    doctree = parse_rst_file(rst)
    assert sorted(find_regions(doctree)) == sorted(regions)
