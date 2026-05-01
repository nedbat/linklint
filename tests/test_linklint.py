from difflib import Differ
from textwrap import dedent
from typing import Any

import pytest

from linklint.linklint import LintIssue, lint_content

from helpers import text_and_id


def diff_lines(text1: str, text2: str) -> str:
    """Return a diff of just the lines that differ between text1 and text2."""
    differ = Differ().compare(
        text1.splitlines(keepends=True),
        text2.splitlines(keepends=True),
    )
    min_diff = "".join(line for line in differ if line.startswith(("-", "+")))
    return min_diff


def lint_test_case(
    *,
    rst: str,
    issues: list[LintIssue],
    diff: str = "",
    id: str = "",
    marks: Any = None,
):
    """Helper to create pytest parameters for linting tests."""
    rst, id = text_and_id(text=rst, id=id)
    if diff.startswith("\n"):
        diff = diff[1:]
    return pytest.param(rst, issues, dedent(diff), id=id, marks=marks or [])


SELF_TEST_CASES = [
    # Check a self-link in the module description.
    lint_test_case(
        id="selflink",
        rst="""
            My Module
            =========

            .. module:: mymodule

            This is the :mod:`mymodule` documentation.

            Also check :mod:`othermodule` for related functionality.

            Other Section
            =============

            This section references :mod:`mymodule` which is fine.
            """,
        issues=[
            LintIssue(6, "self-link to :mod:`mymodule`", fixed=True),
        ],
        diff="""
            - This is the :mod:`mymodule` documentation.
            + This is the :mod:`!mymodule` documentation.
            """,
    ),
    # Is the line-munging correct?
    lint_test_case(
        id="second-section",
        rst="""
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
        issues=[
            LintIssue(11, "self-link to :mod:`mymodule`", fixed=True),
        ],
        diff="""
            - This is the :mod:`mymodule` documentation.
            + This is the :mod:`!mymodule` documentation.
            """,
    ),
    # Check that `.. _module-foo` isn't confused for a module section.
    lint_test_case(
        id="module-target",
        rst="""
            .. _module-xyzzy:

            About Xyzzy
            -----------

            Xyzzy is a magical word that does nothing in particular.
            See :mod:`xyzzy` for more info.
            """,
        issues=[],
    ),
    # Check that headers get fixed too.
    lint_test_case(
        id="header-selflink",
        rst="""
            :mod:`mymodule` Module
            ======================

            .. module:: mymodule

            This is a great module!
            """,
        issues=[
            LintIssue(1, "self-link to :mod:`mymodule`", fixed=True),
        ],
        diff="""
            - :mod:`mymodule` Module
            + :mod:`!mymodule` Module
            - ======================
            + =======================
            """,
    ),
    # Check that overline headers get fixed too.
    lint_test_case(
        id="overline",
        rst="""
            ***********************
            This is :mod:`mymodule`
            ***********************

            .. module:: mymodule

            This is a great module!

            .. deprecated:: 3.8

                Maybe it's not so great after all.
            """,
        issues=[
            LintIssue(2, "self-link to :mod:`mymodule`", fixed=True),
        ],
        diff="""
            - ***********************
            + ************************
            - This is :mod:`mymodule`
            + This is :mod:`!mymodule`
            - ***********************
            + ************************
            """,
    ),
    # Self-link on a continuation line inside a list item.
    lint_test_case(
        id="continuation-line",
        rst="""
            My Module
            =========

            .. module:: mymodule

            - First item talks about something.
              And continues with :mod:`mymodule` here.
            - Second item.
            """,
        issues=[
            LintIssue(7, "self-link to :mod:`mymodule`", fixed=True),
        ],
        diff="""
            -   And continues with :mod:`mymodule` here.
            +   And continues with :mod:`!mymodule` here.
            """,
    ),
    # Don't get confused about sub-modules.
    lint_test_case(
        id="submodule",
        rst="""
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
        issues=[
            LintIssue(line=1, message="self-link to :mod:`dbm`", fixed=True),
            LintIssue(line=11, message="self-link to :mod:`dbm`", fixed=True),
        ],
        diff="""
            - :mod:`dbm` --- Interfaces to Unix "databases"
            + :mod:`!dbm` --- Interfaces to Unix "databases"
            - =============================================
            + ==============================================
            - :mod:`dbm` is a generic interface to variants of the DBM database:
            + :mod:`!dbm` is a generic interface to variants of the DBM database:
            """,
    ),
    # Fix ~ references if needed.
    lint_test_case(
        id="tilde",
        rst="""
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
        issues=[
            LintIssue(line=1, message="self-link to :mod:`email.encoders`", fixed=True),
            LintIssue(line=12, message="self-link to :mod:`email.encoders`", fixed=True),
        ],
        diff="""
            - :mod:`email.encoders`: Encoders
            + :mod:`!email.encoders`: Encoders
            - ----------------------------------
            + --------------------------------
            - :mod:`~email.encoders` module.  These encoders are actually used by the
            + :mod:`!email.encoders` module.  These encoders are actually used by the
            """,
    ),
    # Fix dotted references
    lint_test_case(
        id="dotted",
        rst="""
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
        issues=[
            LintIssue(line=16, message="self-link to :class:`HTMLParser`", fixed=True),
            LintIssue(line=18, message="self-link to :class:`HTMLParser`", fixed=True),
        ],
        diff="""
            -    An :class:`.HTMLParser` instance is fed HTML data and calls handler methods
            +    An :class:`!HTMLParser` instance is fed HTML data and calls handler methods
            -    encountered.  The user should subclass :class:`.HTMLParser` and override its
            +    encountered.  The user should subclass :class:`!HTMLParser` and override its
            """,
    ),
    # Class self-linking.
    lint_test_case(
        id="selflink-class",
        rst="""
            Queue
            =====

            .. class:: Queue(maxsize=0)

               A first in, first out (FIFO) queue.

               .. method:: shutdown(immediate=False)

                  Put a :class:`Queue` instance into a shutdown mode.
            """,
        issues=[
            LintIssue(line=10, message="self-link to :class:`Queue`", fixed=True),
        ],
        diff="""
            -       Put a :class:`Queue` instance into a shutdown mode.
            +       Put a :class:`!Queue` instance into a shutdown mode.
            """,
    ),
    # Some implicit references have no line number?
    # Optional[Anchor] makes a reference to Anchor with no line number and
    # we can't fix it anyway.
    lint_test_case(
        id="implicit-ref",
        rst="""
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
        issues=[],
    ),
    # Some directives had the wrong line number.
    lint_test_case(
        id="note",
        # https://github.com/sphinx-doc/sphinx/pull/14309 fixes the line numbers
        # for versionchanged directives, so our line numbers are off until that
        # is merged.
        marks=pytest.mark.xfail,
        rst="""
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
        issues=[
            LintIssue(line=10, message="self-link to :class:`ZipFile`", fixed=True),
            LintIssue(line=14, message="self-link to :class:`ZipFile`", fixed=True),
        ],
        diff="""
            -       Added the ability to use :class:`ZipFile` as a context manager.
            +       Added the ability to use :class:`!ZipFile` as a context manager.
            -       Added the ability to use :class:`ZipFile` as a context manager.
            +       Added the ability to use :class:`!ZipFile` as a context manager.
            """,
    ),
    # Sometimes there are two to fix in one line.
    lint_test_case(
        id="two-in-one-line",
        rst="""
            ZipFile objects
            ---------------

            .. class:: ZipFile(file, mode='r', compression=ZIP_STORED, allowZip64=True)

               This is :class:`ZipFile` and also :class:`ZipFile` again.
               It's great.
            """,
        issues=[
            LintIssue(line=6, message="self-link to :class:`ZipFile`", fixed=True),
            LintIssue(line=6, message="self-link to :class:`ZipFile`", fixed=True),
        ],
        diff="""
            -    This is :class:`ZipFile` and also :class:`ZipFile` again.
            +    This is :class:`!ZipFile` and also :class:`!ZipFile` again.
            """,
    ),
    # References can be in a section, but still be forward references, so
    # they aren't linking to the section you are already reading.
    lint_test_case(
        id="case-sensitive",
        rst="""
            :mod:`!uuid` --- UUID objects according to :rfc:`9562`
            ======================================================

            .. module:: uuid

            This module provides immutable :class:`UUID` objects (the :class:`UUID` class)
            and :ref:`functions <uuid-factory-functions>` for generating UUIDs corresponding
            to a specific UUID version as specified in :rfc:`9562` (which supersedes :rfc:`4122`),
            for example, :func:`uuid1` for UUID version 1, :func:`uuid3` for UUID version 3, and so on.
            Note that UUID version 2 is deliberately omitted as it is outside the scope of the RFC.

            .. class:: UUID(hex=None, bytes=None, bytes_le=None, fields=None, int=None, version=None, *, is_safe=SafeUUID.unknown)

               Create a UUID from either a string of 32 hexadecimal digits, a string of 16
            """,
        issues=[],
    ),
    # versionchanged directives needed fixing to get the right line numbers,
    # and the inline case needed extra fixing.
    lint_test_case(
        id="inline-versionchanged",
        # https://github.com/sphinx-doc/sphinx/pull/14309 fixes the line numbers
        # for versionchanged directives, so our line numbers are off until that
        # is merged.
        marks=pytest.mark.xfail,
        rst="""
            :mod:`!collections` --- Container datatypes
            ===========================================

            .. module:: collections

            :class:`Counter` objects
            ------------------------

            A counter tool is provided to support convenient and rapid tallies.

            .. class:: Counter([iterable-or-mapping])

                A :class:`!Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.

                .. versionchanged:: 3.7 As a :class:`dict` subclass, :class:`Counter`
                   inherited the capability to remember insertion order.

                Counter objects support additional methods beyond those available for all dictionaries.

            """,
        issues=[
            LintIssue(line=15, message="self-link to :class:`Counter`", fixed=True),
        ],
        diff="""
            -     .. versionchanged:: 3.7 As a :class:`dict` subclass, :class:`Counter`
            +     .. versionchanged:: 3.7 As a :class:`dict` subclass, :class:`!Counter`
            """,
    ),
    # A newline at the end of a link is trimmed, so our line count was off.
    lint_test_case(
        id="newline-in-link",
        rst="""
            .. function:: fwalk(top='.', topdown=True, onerror=None, *, follow_symlinks=False, dir_fd=None)

               This function always supports :ref:`paths relative to directory descriptors
               <dir_fd>` and :ref:`not following symlinks <follow_symlinks>`.  Note however
               that, unlike other functions, the :func:`fwalk` default value for
               *follow_symlinks* is ``False``.

               This function always supports :ref:`paths relative to directory descriptors
               <dir_fd>`.  Note however that the :func:`fwalk` default value for
               *follow_symlinks* is ``False``.

            .. function:: expm1(x)

               Return *e* raised to the power *x*, minus 1.  Here *e* is the base of natural
               logarithms.  For small floats *x*, the subtraction in ``exp(x) - 1``
               can result in a `significant loss of precision
               <https://en.wikipedia.org/wiki/Loss_of_significance>`_; the :func:`expm1`
               function provides a way to compute this quantity to full precision.

            """,
        issues=[
            LintIssue(line=5, message="self-link to :func:`fwalk`", fixed=True),
            LintIssue(line=9, message="self-link to :func:`fwalk`", fixed=True),
            LintIssue(line=17, message="self-link to :func:`expm1`", fixed=True),
        ],
        diff="""
            -    that, unlike other functions, the :func:`fwalk` default value for
            +    that, unlike other functions, the :func:`!fwalk` default value for
            -    <dir_fd>`.  Note however that the :func:`fwalk` default value for
            +    <dir_fd>`.  Note however that the :func:`!fwalk` default value for
            -    <https://en.wikipedia.org/wiki/Loss_of_significance>`_; the :func:`expm1`
            +    <https://en.wikipedia.org/wiki/Loss_of_significance>`_; the :func:`!expm1`
            """,
    ),
    lint_test_case(
        id="stars",
        rst=r"""
            Process Management
            ------------------

            These functions may be used to create and manage processes.

            The various :func:`exec\* <execl>` functions take a list of arguments for the new
            program loaded into the process.

            .. function:: execl(path, arg0, arg1, ...)
                          execle(path, arg0, arg1, ..., env)
                          execlp(file, arg0, arg1, ...)
                          execlpe(file, arg0, arg1, ..., env)
                          execv(path, args)
                          execve(path, args, env)
                          execvp(file, args)
                          execvpe(file, args, env)

               The current process is replaced immediately. Open file objects and
               descriptors are not flushed, so if there may be data buffered
               on these open files, you should flush them using
               :func:`sys.stdout.flush` or :func:`os.fsync` before calling an
               :func:`exec\* <execl>` function.

               The "l" and "v" variants of the :func:`exec\* <execl>` functions differ in how
               command-line arguments are passed.  The "l" variants are perhaps the easiest
               to work with if the number of parameters is fixed when the code is written; the
               individual parameters simply become additional parameters to the :func:`!execl\*`
               functions.  The "v" variants are good when the number of parameters is
               variable, with the arguments being passed in a list or tuple as the *args*
               parameter.  In either case, the arguments to the child process should start with
               the name of the command being run, but this is not enforced.

               The variants which include a "p" near the end (:func:`execlp`,
               :func:`execlpe`, :func:`execvp`, and :func:`execvpe`) will use the
               :envvar:`PATH` environment variable to locate the program *file*.
            """,
        issues=[
            LintIssue(line=22, message="self-link to :func:`execl`", fixed=True),
            LintIssue(line=24, message="self-link to :func:`execl`", fixed=True),
            LintIssue(line=33, message="self-link to :func:`execlp`", fixed=True),
            LintIssue(line=34, message="self-link to :func:`execlpe`", fixed=True),
            LintIssue(line=34, message="self-link to :func:`execvp`", fixed=True),
            LintIssue(line=34, message="self-link to :func:`execvpe`", fixed=True),
        ],
        diff=r"""
            -    :func:`exec\* <execl>` function.
            +    :func:`!exec\*` function.
            -    The "l" and "v" variants of the :func:`exec\* <execl>` functions differ in how
            +    The "l" and "v" variants of the :func:`!exec\*` functions differ in how
            -    The variants which include a "p" near the end (:func:`execlp`,
            +    The variants which include a "p" near the end (:func:`!execlp`,
            -    :func:`execlpe`, :func:`execvp`, and :func:`execvpe`) will use the
            +    :func:`!execlpe`, :func:`!execvp`, and :func:`!execvpe`) will use the
            """,
    ),
    # A class mention in a method signature creates a reference with no line number, which
    # used to cause an assertion. But also, there's no markup for us to fix,
    # so it creates a LintIssue with fixed=False.
    lint_test_case(
        id="class-in-signature",
        rst="""
            Snapshot
            ^^^^^^^^

            .. class:: Snapshot

               Snapshot of traces of memory blocks allocated by Python.

               The :func:`take_snapshot` function creates a snapshot instance.

               .. method:: compare_to(old_snapshot: Snapshot, key_type: str, cumulative: bool=False)

                  Compute the differences with an old snapshot. Get statistics as a sorted
                  list of :class:`StatisticDiff` instances grouped by *key_type*.
            """,
        issues=[
            LintIssue(line=10, message="self-link to :class:`Snapshot`", fixed=False),
        ],
    ),
    lint_test_case(
        rst="classhier",
        issues=[
            LintIssue(line=6, message="self-link to :class:`ClassA`", fixed=True),
            LintIssue(line=10, message="self-link to :class:`ClassA`", fixed=True),
            LintIssue(line=10, message="self-link to :meth:`methoda1`", fixed=True),
            LintIssue(line=14, message="self-link to :class:`ClassA`", fixed=True),
            LintIssue(line=18, message="self-link to :meth:`methodb1`", fixed=True),
            LintIssue(line=19, message="self-link to :class:`ClassA`", fixed=True),
            LintIssue(line=24, message="self-link to :class:`ClassA`", fixed=True),
            LintIssue(line=28, message="self-link to :meth:`methoda2`", fixed=True),
        ],
        diff=r"""
            -     An outer class, called :class:`ClassA`.
            +     An outer class, called :class:`!ClassA`.
            -         A method of :class:`ClassA`, called :meth:`methoda1`.
            +         A method of :class:`!ClassA`, called :meth:`!methoda1`.
            -         A nested class. This is inside :class:`ClassA`.
            +         A nested class. This is inside :class:`!ClassA`.
            -             A method of :class:`ClassB`, called :meth:`methodb1`.
            +             A method of :class:`ClassB`, called :meth:`!methodb1`.
            -             We're still inside :class:`ClassA`.
            +             We're still inside :class:`!ClassA`.
            -         We're still inside :class:`ClassA`.
            +         We're still inside :class:`!ClassA`.
            -     A method of :class:`ClassA`, called :meth:`methoda2`.
            +     A method of :class:`ClassA`, called :meth:`!methoda2`.
        """,
    ),
    lint_test_case(
        id="method-no-class",
        rst="""
            Memory-mapped file objects behave like both :class:`bytearray` and like
            :term:`file objects <file object>`.  You can use mmap objects in most places
            where :class:`bytearray` are expected; for example, you can use the :mod:`re`
            module to search through a memory-mapped file.  You can also change a single
            byte by doing ``obj[index] = 97``, or change a subsequence by assigning to a
            slice: ``obj[i1:i2] = b'...'``.  You can also read and write data starting at
            the current file position, and :meth:`seek` through the file to different positions.

            The easiest way to create a text stream is with :meth:`open`, optionally
            specifying an encoding.
            """,
        issues=[],
    ),
    lint_test_case(
        rst="frozenset",
        issues=[
            LintIssue(line=11, message="self-link to :class:`frozenset`", fixed=True),
        ],
        diff="""
            -    represent sets of sets, the inner sets must be :class:`frozenset`
            +    represent sets of sets, the inner sets must be :class:`!frozenset`
        """,
    ),
]


@pytest.mark.parametrize("rst, issues, diff", SELF_TEST_CASES)
def test_fix_self_link(rst: str, issues: list[LintIssue], diff: str) -> None:
    result = lint_content(rst, fix=True, checks={"self"})
    assert result.issues == issues
    assert diff_lines(rst, result.content) == diff


@pytest.mark.parametrize("rst, issues, diff", SELF_TEST_CASES)
def test_nofix_self_link(rst: str, issues: list[LintIssue], diff: str) -> None:
    result = lint_content(rst, fix=False, checks={"self"})
    issues = [LintIssue(issue.line, issue.message, fixed=False) for issue in issues]
    assert result.issues == issues
    assert rst == result.content


PARADUP_TEST_CASES = [
    lint_test_case(
        id="class-in-signature",
        rst="""
            LogRecord Objects
            -----------------

            :class:`LogRecord` instances are created automatically by the :class:`Logger`
            every time something is logged, and can be created manually via
            :func:`makeLogRecord` (for example, from a pickled event received over the
            wire).

            .. class:: LogRecord(name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None)

               Contains all the information pertinent to the event being logged.

               :param args: Variable data to merge into the *msg* argument
                  to obtain the event description.
               :type args: tuple | dict[str, typing.Any]

               :param exc_info: An exception tuple with the current exception information,
                  as returned by :func:`sys.exc_info`,
                  or ``None`` if no exception information is available.
               :type exc_info: tuple[type[BaseException], BaseException, types.TracebackType] | None

               :param func: The name of the function or method
                  from which the logging call was invoked.
               :type func: str | None
            """,
        issues=[
            # Strange: line 2 is the underline of the header, the :param: is miles away.
            LintIssue(line=2, message="duplicate :class:`BaseException` in paragraph", fixed=False)
        ],
    ),
    lint_test_case(
        id="paragraphs",
        rst="""
            1 Multiple links to :class:`Something` in the same paragraph about
            :class:`Something` are not a problem, but they do create multiple
            LintIssues on different lines about :class:`Something`.

            5 If :class:`!Something` is referenced
            but not linked, then :class:`Something` could
            be the first link to :class:`Something` and the other links
            to :class:`Something` are duplicates.
            """,
        issues=[
            LintIssue(line=2, message="duplicate :class:`Something` in paragraph", fixed=False),
            LintIssue(line=3, message="duplicate :class:`Something` in paragraph", fixed=False),
            LintIssue(line=7, message="duplicate :class:`Something` in paragraph", fixed=False),
            LintIssue(line=8, message="duplicate :class:`Something` in paragraph", fixed=False),
        ],
    ),
    lint_test_case(
        id="lists",
        rst="""
            Some lists:

            - 3 Multiple links to :class:`Something` in the same paragraph about
              :class:`Something` are not a problem, but they do create multiple
              LintIssues on different lines about :class:`Something`.

            - 7 If :class:`!Something` is referenced
              but not linked, then :class:`Something` could
              be the first link to :class:`Something` and the other links
              to :class:`Something` are duplicates.
            """,
        issues=[
            LintIssue(line=4, message="duplicate :class:`Something` in paragraph", fixed=False),
            LintIssue(line=5, message="duplicate :class:`Something` in paragraph", fixed=False),
            LintIssue(line=9, message="duplicate :class:`Something` in paragraph", fixed=False),
            LintIssue(line=10, message="duplicate :class:`Something` in paragraph", fixed=False),
        ],
    ),
]


@pytest.mark.parametrize("rst, issues, diff", PARADUP_TEST_CASES)
def test_paradup(rst: str, issues: list[LintIssue], diff: str) -> None:
    assert diff == ""
    result = lint_content(rst, fix=False, checks={"paradup"})
    assert result.issues == issues
