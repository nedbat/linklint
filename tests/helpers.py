"""Make tests a little nicer."""

from pathlib import Path
from textwrap import dedent


def text_and_id(*, text: str, id: str = ""):
    """Helper to create pytest parameters for tests."""
    assert text, "Test cases must have text content or a file name"
    if "\n" in text:
        assert text.startswith("\n"), "Don't start text with a backslash"
        text = dedent(text[1:])
    else:
        # It's a file name
        assert not id, "Don't provide filename and id"
        id = text
        text = (Path(__file__).parent / "data" / text).read_text()
    assert id, "Test cases must have an id"
    return text, id
