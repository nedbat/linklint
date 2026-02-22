import contextlib
import os
import re
import tempfile


def test_slug() -> str:
    test_name = os.getenv("PYTEST_CURRENT_TEST", "unknown")
    m = re.search(r"::(?P<test>[\w_]+)(?P<param>\[[-._+/\w]+\])?(?: \(\w+\))$", test_name)
    assert m is not None
    if param := m["param"]:
        return param.strip("[]")
    return m["test"]


@contextlib.contextmanager
def in_tempdir():
    with tempfile.TemporaryDirectory() as tmpdir:
        with contextlib.chdir(tmpdir):
            yield
