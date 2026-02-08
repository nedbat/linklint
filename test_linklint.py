from collections import namedtuple
from dataclasses import dataclass
from difflib import Differ
from textwrap import dedent

import pytest

from linklint import LintIssue, lint_content


LintTestCase = namedtuple(
    "LintTestCase",
    ["rst", "expected_issues", "diff"],
)


@pytest.mark.parametrize(
    "rst, expected_issues, diff",
    [
        # Check a self-link in the module description.
        LintTestCase(
            rst="""\
                My Module
                =========

                .. module:: mymodule

                This is the :mod:`mymodule` documentation.

                Also check :mod:`othermodule` for related functionality.

                Other Section
                =============

                This section references :mod:`mymodule` which is fine.
                """,
            expected_issues=[
                LintIssue(6, "self-link to module 'mymodule'", fixed=True),
            ],
            diff="""\
                - This is the :mod:`mymodule` documentation.
                + This is the :mod:`!mymodule` documentation.
            """,
        ),
        # Is the line-munging correct?
        LintTestCase(
            rst="""\
                Another
                =======

                Look at :mod:`mymodule` for more info.

                My Module
                =========

                .. module:: mymodule

                This is the :mod:`mymodule` documentation.

                Also check :mod:`othermodule` for related functionality.

                Other Section
                =============

                This section references :mod:`mymodule` which is fine.
                """,
            expected_issues=[
                LintIssue(11, "self-link to module 'mymodule'", fixed=True),
            ],
            diff="""\
                - This is the :mod:`mymodule` documentation.
                + This is the :mod:`!mymodule` documentation.
            """,
        ),
        # Check that `.. _module-foo` isn't confused for a module section.
        LintTestCase(
            rst="""\
                .. _module-xyzzy:

                About Xyzzy
                -----------

                Xyzzy is a magical word that does nothing in particular.
                See :mod:`xyzzy` for more info.
                """,
            expected_issues=[],
            diff="",
        ),
        # Check that headers get fixed too.
        LintTestCase(
            rst="""\
                :mod:`mymodule` Module
                ======================

                .. module:: mymodule

                This is a great module!
                """,
            expected_issues=[
                LintIssue(1, "self-link to module 'mymodule'", fixed=True),
            ],
            diff="""\
                - :mod:`mymodule` Module
                + :mod:`!mymodule` Module
                - ======================
                + =======================
            """,
        ),
        # Self-link on a continuation line inside a list item.
        LintTestCase(
            rst="""\
                My Module
                =========

                .. module:: mymodule

                - First item talks about something.
                  And continues with :mod:`mymodule` here.
                - Second item.
                """,
            expected_issues=[
                LintIssue(7, "self-link to module 'mymodule'", fixed=True),
            ],
            diff="""\
                -   And continues with :mod:`mymodule` here.
                +   And continues with :mod:`!mymodule` here.
            """,
        ),
    ],
)
def test_self_link(rst, expected_issues, diff):
    rst = dedent(rst)
    result = lint_content(rst, fix=True)
    assert result.issues == expected_issues
    differ = Differ().compare(
        rst.splitlines(keepends=True),
        result.content.splitlines(keepends=True),
    )
    min_diff = "".join(l for l in differ if l.startswith(("-", "+")))
    assert min_diff == dedent(diff)
