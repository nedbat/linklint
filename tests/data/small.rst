Linklint sample page
====================

This is a page to test the linklint extension.


.. class:: MyClass

    The :class:`MyClass` class is a sample class to test the linklint extension.

.. class:: AnotherClass

    Sometimes :class:`AnotherClass` uses methods from :class:`MyClass`.

.. function:: my_thing()

    This is about :func:`my_thing`, which is a sample function to test the
    linklint extension. It will have the same name as :mod:`my_thing`, to see
    if linklint can distinguish between them.

:mod:`my_thing`: My thing module
--------------------------------

.. module:: my_thing

    This is about :mod:`my_thing`, which is a sample module to test the
    linklint extension. This page used to have ``:func:`my_thing```, but it
    turns out Sphinx doesn't distinguish between the function and module, so I
    took it out.
