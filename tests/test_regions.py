import pytest

from linklint.regions import Region, find_regions
from linklint.rsthelp import parse_rst

from helpers import text_and_id


def region_test_case(*, rst: str, regions: list[Region], id: str = ""):
    """Helper to create pytest parameters for tests."""
    rst, id = text_and_id(text=rst, id=id)
    return pytest.param(rst, regions, id=id)


def region(
    kind: str,
    name: str,
    *,
    start: int,
    end: int = 0,
    end_main: int = 0,
    end_total: int = 0,
) -> Region:
    """Helper to create a Region with end_main and end_total defaulting to end."""
    assert end or (end_main and end_total), (
        "Either end or both end_main and end_total must be provided"
    )
    if not end_main:
        end_main = end
    if not end_total:
        end_total = end
    return Region(kind=kind, name=name, start=start, end_main=end_main, end_total=end_total)


TEST_CASES = [
    # The `contents::` directive makes unnumbered paragraphs.
    region_test_case(
        id="unnumbered",
        rst="""
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
    region_test_case(
        id="mymodule",
        rst="""
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
        regions=[
            region("module", "mymodule", start=1, end=18),
        ],
    ),
    region_test_case(
        id="multiple-functions",
        rst=r"""
            The various :func:`exec\* <execl>` functions take a list of arguments for the new
            program loaded into the process.

            .. function:: execl(path, arg0, arg1, ...)
                          execle(path, arg0, arg1, ..., env)
                          execlp(file, arg0, arg1, ...)
                          execlpe(file, arg0, arg1, ..., env)

               This is a family of similar functions.
            """,
        regions=[
            region("function", "execl", start=4, end=9),
            region("function", "execle", start=4, end=9),
            region("function", "execlp", start=4, end=9),
            region("function", "execlpe", start=4, end=9),
        ],
    ),
    region_test_case(
        rst="lzma.rst",
        regions=[
            region("exception", "LZMAError", start=26, end=29),
            region("function", "open", start=35, end=68),
            region("method", "LZMAFile.peek", start=108, end=117),
            region("attribute", "LZMAFile.mode", start=119, end=123),
            region("attribute", "LZMAFile.name", start=125, end=130),
            region("class", "LZMAFile", start=71, end_main=107, end_total=141),
            region("method", "LZMACompressor.compress", start=209, end=215),
            region("method", "LZMACompressor.flush", start=217, end=222),
            region("class", "LZMACompressor", start=147, end_main=208, end_total=222),
            region("method", "LZMADecompressor.decompress", start=254, end=279),
            region("attribute", "LZMADecompressor.check", start=281, end=285),
            region("attribute", "LZMADecompressor.eof", start=287, end=289),
            region("attribute", "LZMADecompressor.unused_data", start=291, end=295),
            region("attribute", "LZMADecompressor.needs_input", start=297, end=302),
            region("class", "LZMADecompressor", start=225, end_main=253, end_total=302),
            region("function", "compress", start=304, end=310),
            region("function", "decompress", start=313, end=322),
            region("function", "is_check_supported", start=328, end=335),
            region("module", "lzma", start=1, end_main=25, end_total=346),
        ],
    ),
]


@pytest.mark.parametrize("rst, regions", TEST_CASES)
def test_regions(rst: str, regions: list[Region]) -> None:
    assert sorted(find_regions(parse_rst(rst))) == sorted(regions)
