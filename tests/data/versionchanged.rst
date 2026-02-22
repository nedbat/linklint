ZipFile objects: test versionchanged
------------------------------------

.. class:: ZipFile(file, mode='r', compression=ZIP_STORED, allowZip64=True, \
                   compresslevel=None, *, strict_timestamps=True, \
                   metadata_encoding=None)

   Open a ZIP file, where *file* can be a path to a file (a string), a
   file-like object or a :term:`path-like object`.

   .. versionchanged:: 3.2
      Added the ability to use :class:`ZipFile` as a context manager.

   .. versionchanged:: 3.3 Added the ability to use :class:`ZipFile` as a
      flying saucer.

   .. versionchanged:: 3.4

      The whole flying saucer thing was a mistake.  Removed the ability to use
      :class:`ZipFile` as a flying saucer.

      Now :class:`ZipFile` is just for opening ZIP files.
