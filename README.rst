========
Linklint
========

Linklint checks .rst files for excessive links to references.

It also can be used as a Sphinx extension to automatically unlink references
that should not be links.


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

During the build process, linklint will run all its checks and unlink any
reference it considers excessive.


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
files to unlink excessive references.  Linklint unlinks references by changing
``:func:`foo``` to ``:func:`!foo```.

If you agree with linklint's decisions, the Sphinx extension is a better
option, since it doesn't require changing the source files, and doesn't
hard-code the decisions.


Changes
=======

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
