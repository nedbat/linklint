Class hierarchy
---------------

.. class:: ClassA(one, two)

    An outer class, called :class:`ClassA`.

    .. method:: methoda1()

        A method of :class:`ClassA`, called :meth:`methoda1`.

    .. class:: ClassB(three, four)

        A nested class. This is inside :class:`ClassA`.

        .. method:: methodb1()

            A method of :class:`ClassB`, called :meth:`methodb1`. We're still
            inside :class:`ClassA`.

    .. method:: ClassB.methodb2()

        A method of :class:`ClassB`, called :meth:`methodb2`. We're still
        inside :class:`ClassA`.

.. method:: ClassA.methoda2()

    A method of :class:`ClassA`, called :meth:`methoda2`.
