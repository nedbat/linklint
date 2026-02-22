========
linklint
========

Linklint checks .rst files for inappropriate links.

It also can be used as a Sphinx extension to automatically unlink references
that should not be links.


Changes
=======

Unreleased
----------

Now available as a Sphinx extension. Instead of changing .rst source files,
the excessive links are automatically unlinked in the generated documentation.

0.1.0 – 2026-02-21
------------------

First version: works as a linter with ``--check`` and ``--fix`` to change .rst
source files.
