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
            id="overline",
            rst="""\
                ***********************
                This is :mod:`mymodule`
                ***********************

                .. module:: mymodule

                This is a great module!

                .. deprecated:: 3.8

                    Maybe it's not so great after all.
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
        # Fix ~ references if needed.
        LintTestCase(
            id="tilde",
            rst="""\
                :mod:`email.encoders`: Encoders
                ----------------------------------

                .. module:: email.encoders

                This module is deprecated in Python 3.  The functions provided here
                should not be called explicitly since the :class:`~email.mime.text.MIMEText`
                class sets the content type and CTE header using the *_subtype* and *_charset*
                values passed during the instantiation of that class.

                The :mod:`email` package provides some convenient encoders in its
                :mod:`~email.encoders` module.  These encoders are actually used by the
                :class:`~email.mime.audio.MIMEAudio` and :class:`~email.mime.image.MIMEImage`
                class constructors to provide default encodings.
                """,
            expected_issues=[
                LintIssue(
                    line=1,
                    message="self-link to module 'email.encoders'",
                    fixed=True,
                ),
                LintIssue(
                    line=12,
                    message="self-link to module 'email.encoders'",
                    fixed=True,
                ),
            ],
            diff="""\
                - :mod:`email.encoders`: Encoders
                + :mod:`!email.encoders`: Encoders
                - ----------------------------------
                + --------------------------------
                - :mod:`~email.encoders` module.  These encoders are actually used by the
                + :mod:`!encoders` module.  These encoders are actually used by the
            """,
        ),
        # Fix dotted references
        LintTestCase(
            id="dotted",
            rst="""\
                :mod:`!html.parser` --- Simple HTML and XHTML parser
                ====================================================

                .. module:: html.parser
                   :synopsis: A simple parser that can handle HTML and XHTML.

                --------------

                This module defines a class :class:`HTMLParser` which serves as the basis for
                parsing text files formatted in HTML (HyperText Mark-up Language) and XHTML.

                .. class:: HTMLParser(*, convert_charrefs=True, scripting=False)

                   Create a parser instance able to parse invalid markup.

                   An :class:`.HTMLParser` instance is fed HTML data and calls handler methods
                   when start tags, end tags, text, comments, and other markup elements are
                   encountered.  The user should subclass :class:`.HTMLParser` and override its
                   methods to implement the desired behavior.
            """,
            expected_issues=[
                LintIssue(
                    line=9, message="self-link to class 'HTMLParser'", fixed=True
                ),
                LintIssue(
                    line=16, message="self-link to class 'HTMLParser'", fixed=True
                ),
                LintIssue(
                    line=18, message="self-link to class 'HTMLParser'", fixed=True
                ),
            ],
            diff="""\
                - This module defines a class :class:`HTMLParser` which serves as the basis for
                + This module defines a class :class:`!HTMLParser` which serves as the basis for
                -    An :class:`.HTMLParser` instance is fed HTML data and calls handler methods
                +    An :class:`!HTMLParser` instance is fed HTML data and calls handler methods
                -    encountered.  The user should subclass :class:`.HTMLParser` and override its
                +    encountered.  The user should subclass :class:`!HTMLParser` and override its
            """,
        ),
        # Class self-linking.
        LintTestCase(
            id="selflink-class",
            rst="""\
                Queue
                =====

                .. class:: Queue(maxsize=0)

                A first in, first out (FIFO) queue.

                .. method:: shutdown(immediate=False)

                    Put a :class:`Queue` instance into a shutdown mode.
                """,
            expected_issues=[
                LintIssue(line=10, message="self-link to class 'Queue'", fixed=True),
            ],
            diff="""\
                -     Put a :class:`Queue` instance into a shutdown mode.
                +     Put a :class:`!Queue` instance into a shutdown mode.
            """,
        ),
        # Some implicit references have no line number?
        # Optional[Anchor] makes a reference to Anchor with no line number and
        # we can't fix it anyway.
        LintTestCase(
            id="implicit-ref",
            rst="""\
                :mod:`!importlib.resources` -- Package resource reading, opening and access
                ---------------------------------------------------------------------------

                .. module:: importlib.resources

                .. class:: Anchor

                    Represents an anchor for resources, either a :class:`module object
                    <types.ModuleType>` or a module name as a string. Defined as
                    ``Union[str, ModuleType]``.

                .. function:: files(anchor: Optional[Anchor] = None)

                    *anchor* is an optional :class:`Anchor`. If the anchor is a
                    package, resources are resolved from that package. If a module,
                    resources are resolved adjacent to that module (in the same package
                    or the package root). If the anchor is omitted, the caller's module
                    is used.
                """,
            expected_issues=[
                LintIssue(line=14, message="self-link to class 'Anchor'", fixed=True),
            ],
            diff="""\
                -     *anchor* is an optional :class:`Anchor`. If the anchor is a
                +     *anchor* is an optional :class:`!Anchor`. If the anchor is a
            """,
        ),
        # Some directives had the wrong line number.
        LintTestCase(
            id="note",
            rst="""\
                ZipFile objects
                ---------------

                .. class:: ZipFile(file, mode='r', compression=ZIP_STORED, allowZip64=True)

                   Open a ZIP file, where *file* can be a path to a file (a string), a
                   file-like object or a :term:`path-like object`.

                   .. versionchanged:: 3.2
                      Added the ability to use :class:`ZipFile` as a context manager.
                      Also did many other good things.

                   .. note::
                      Added the ability to use :class:`ZipFile` as a context manager.
                      Also did many other good things.
                """,
            expected_issues=[
                LintIssue(line=10, message="self-link to class 'ZipFile'", fixed=True),
                LintIssue(line=14, message="self-link to class 'ZipFile'", fixed=True),
            ],
            diff="""\
                -       Added the ability to use :class:`ZipFile` as a context manager.
                +       Added the ability to use :class:`!ZipFile` as a context manager.
                -       Added the ability to use :class:`ZipFile` as a context manager.
                +       Added the ability to use :class:`!ZipFile` as a context manager.
            """,
        ),
        # Sometimes there are two to fix in one line.
        LintTestCase(
            id="two-in-one-line",
            rst="""\
                ZipFile objects
                ---------------

                .. class:: ZipFile(file, mode='r', compression=ZIP_STORED, allowZip64=True)

                   This is :class:`ZipFile` and also :class:`ZipFile` again.
                   It's great.
                """,
            expected_issues=[
                LintIssue(line=6, message="self-link to class 'ZipFile'", fixed=True),
                LintIssue(line=6, message="self-link to class 'ZipFile'", fixed=True),
            ],
            diff="""\
                -    This is :class:`ZipFile` and also :class:`ZipFile` again.
                +    This is :class:`!ZipFile` and also :class:`!ZipFile` again.
            """,
        ),
    ],
)
def test_self_link(rst, expected_issues, diff):
    result = lint_content(rst, fix=True, checks={"self", "selfclass"})
    assert result.issues == expected_issues
    assert diff_lines(rst, result.content) == diff
