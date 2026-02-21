from linklint.rsthelp import is_header_line

import pytest


@pytest.mark.parametrize(
    "hline, is_header",
    [
        ("======", True),
        ("------", True),
        ("======  ", True),     # Trailing space is ok
        ("======\n", True),     # Newline is ok
        ("  ======  ", False),  # Can't be indented
        ("====", False),        # Too short
        ("===========", True),  # Longer is ok
        ("=====-", False),      # Mixed chars
        ("123456", False),      # Not punctuation
    ],
)
def test_is_header_line(hline: str, is_header: bool) -> None:
    assert is_header_line(hline, "Header") == is_header
