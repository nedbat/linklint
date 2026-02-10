from difflib import Differ
from textwrap import dedent

import pytest

from linklint import LintIssue, lint_content


def diff_lines(text1, text2):
    """Return a diff of just the lines that differ between text1 and text2."""
    differ = Differ().compare(
        text1.splitlines(keepends=True),
        text2.splitlines(keepends=True),
    )
    min_diff = "".join(line for line in differ if line.startswith(("-", "+")))
    return min_diff


def LintTestCase(*, rst, expected_issues, diff, id=None):
    """Helper to create pytest parameters for linting tests."""
    return pytest.param(
        dedent(rst),
        expected_issues,
        dedent(diff),
        id=id,
    )


@pytest.mark.parametrize(
    "rst, expected_issues, diff",
    [
        # Check a self-link in the module description.
        LintTestCase(
            id="selflink",
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
            id="second-section",
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
            id="module-target",
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
            id="header-selflink",
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
        # Check that overline headers get fixed too.
        LintTestCase(
            id="header-selflink",
            rst="""\
                ***********************
                This is :mod:`mymodule`
                ***********************

                .. module:: mymodule

                This is a great module!
                """,
            expected_issues=[
                LintIssue(2, "self-link to module 'mymodule'", fixed=True),
            ],
            diff="""\
                - ***********************
                + ************************
                - This is :mod:`mymodule`
                + This is :mod:`!mymodule`
                - ***********************
                + ************************
            """,
        ),
        # Self-link on a continuation line inside a list item.
        LintTestCase(
            id="continuation-line",
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
        # Don't get confused about sub-modules.
        LintTestCase(
            id="submodule",
            rst="""\
                :mod:`dbm` --- Interfaces to Unix "databases"
                =============================================

                .. module:: dbm
                :synopsis: Interfaces to various Unix "database" formats.

                **Source code:** :source:`Lib/dbm/__init__.py`

                --------------

                :mod:`dbm` is a generic interface to variants of the DBM database:

                * :mod:`dbm.sqlite3`
                * :mod:`dbm.gnu`
                * :mod:`dbm.ndbm`

                If none of these modules are installed, the
                slow-but-simple implementation in module :mod:`dbm.dumb` will be used. There
                is a `third party interface <https://www.jcea.es/programacion/pybsddb.htm>`_ to
                the Oracle Berkeley DB.

                .. note::
                None of the underlying modules will automatically shrink the disk space used by
                the database file. However, :mod:`dbm.sqlite3`, :mod:`dbm.gnu` and :mod:`dbm.dumb`
                provide a :meth:`!reorganize` method that can be used for this purpose.
                """,
            expected_issues=[
                LintIssue(line=1, message="self-link to module 'dbm'", fixed=True),
                LintIssue(line=11, message="self-link to module 'dbm'", fixed=True),
            ],
            diff="""\
                - :mod:`dbm` --- Interfaces to Unix "databases"
                + :mod:`!dbm` --- Interfaces to Unix "databases"
                - =============================================
                + ==============================================
                - :mod:`dbm` is a generic interface to variants of the DBM database:
                + :mod:`!dbm` is a generic interface to variants of the DBM database:
            """,
        ),
    ],
)
def test_self_link(rst, expected_issues, diff):
    result = lint_content(rst, fix=True)
    assert result.issues == expected_issues
    assert diff_lines(rst, result.content) == diff
