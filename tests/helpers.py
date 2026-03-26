"""Make tests a little nicer."""

import tomllib
from pathlib import Path
from textwrap import dedent


PROJECT = Path(__file__).parent.parent
DATA_DIR = PROJECT / "tests/data"


def read_toml(name: str) -> dict[str, str]:
    """Read a .toml test data file.

    All values are strings, and are dedented.
    """
    with (DATA_DIR / f"{name}.toml").open("rb") as f:
        data = tomllib.load(f)
    return {k: dedent(v) for k, v in data.items()}


def text_and_id(*, text: str, id: str = ""):
    """Helper to create pytest parameters for tests."""
    assert text, "Test cases must have text content or a file name"
    if "\n" in text:
        assert text.startswith("\n"), "Don't start text with a backslash"
        text = dedent(text[1:])
    else:
        # It's a data file name
        assert not id, "Don't provide filename and id"
        id = text
        text = read_toml(text)["rst"]
    assert id, "Test cases must have an id"
    return text, id
