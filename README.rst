========
linklint
========

Linklint checks .rst files for inappropriate links.

It also can be used as a Sphinx extension to automatically unlink references
that should not be links.


Changes
=======

0.3.0 – 2026-02-28
------------------

Methods are associated with classes properly in a number of ways.

The Sphinx extension now displays the number of references that were unlinked.
The CPython docs report 3612 references unlinked.

0.2.0 – 2026-02-22
------------------

Now available as a Sphinx extension. Instead of changing .rst source files,
the excessive links are automatically unlinked in the generated documentation.

0.1.0 – 2026-02-21
------------------

First version: works as a linter with ``--check`` and ``--fix`` to change .rst
source files.
