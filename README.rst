========
Linklint
========

Linklint is a Sphinx extension that removes links from excessive references.

It also can be used as command-line linter to find or correct those references
in .rst files.


Checks
======

Linklint has two different checks:

- ``self``: find references that link to their own section. For example, in the
  description of a class, use `:class:` referring to itself. These should not
  be links since they will not take you someplace new.

- ``paradup``: find multiple identical references within a single paragraph.
  The first should be a link, but subsequent references don't need to be links,
  they are just distractions.


Sphinx extension
================

To use linklint as a Sphinx extension, add it to the ``extensions`` list in
your ``conf.py`` file:

.. code:: python

    extensions = [
        # .. probably other extensions are already here..
        "linklint.ext",
    ]

During the build process, linklint will run its checks and remove links from
references it considers excessive. No changes are made to the source files.


Command-line use
================

You can use linklint as a command-line linter::

    % linklint --help
    usage: linklint [-h] [--check CHECK] [--fix] files [files ...]

    positional arguments:
      files          RST files to lint

    options:
      -h, --help     show this help message and exit
      --check CHECK  comma-separated checks to run (self, paradup, all)
      --fix          Fix the issues in place

This can be useful to see what linklint considers excessive, or to modify .rst
files to unlink excessive references. Where it can, Linklint unlinks references
by changing ``:func:`foo``` to ``:func:`!foo```.

If you agree with linklint's decisions, the Sphinx extension is a better
option, since it doesn't require changing the source files, and doesn't
hard-code the decisions.

Testing on CPython
==================

To try local changes in the CPython docs::

    cd python/cpython/Docs
    make clean venv html
    mv build build0
    sed -i '' "/linklint/s@.*@-e $HOME/linklint@" requirements.txt
    make clean venv
    uv pip install -r requirements.txt
    make html
    meld build0/html build/html
    # or
    diff -I 'Last updated on' -r build0/html build/html


Changes
=======

v1.0.0 (2026-05-02)
-------------------

Fix: the `:noindex:` directive was ignored, so sections marked as such were
considered targets when they shouldn't have been. This is now fixed.

v0.4.1 (2026-03-27)
-------------------

Linklint v0.4.0 required Sphinx 9.x, which prevented it from being used by the
CPython docs. Now linklint will work with Sphinx 8.x as well.

v0.4.0 (2026-03-10)
-------------------

A number of roles (``:ref:``, ``:doc:`` and others) were being unlinked when
they seemed excessive, but shouldn't have been. They are explicit references to
other parts of the documentation, so should never be removed. This is now
fixed.

v0.3.1 (2026-03-01)
-------------------

Published to PyPI.

v0.3.0 (2026-02-28)
-------------------

Methods are associated with classes properly in a number of ways.

The Sphinx extension now displays the number of references that were unlinked.
The CPython docs report 3612 references unlinked.

v0.2.0 (2026-02-22)
-------------------

Now available as a Sphinx extension. Instead of changing .rst source files,
the excessive links are automatically unlinked in the generated documentation.

v0.1.0 (2026-02-21)
-------------------

First version: works as a linter with ``--check`` and ``--fix`` to change .rst
source files.
