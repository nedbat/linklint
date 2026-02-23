ZipFile objects
---------------


.. class:: ZipFile(file, mode='r', compression=ZIP_STORED, allowZip64=True, \
                   compresslevel=None, *, strict_timestamps=True, \
                   metadata_encoding=None)

   Open a ZIP file, where *file* can be a path to a file (a string), a
   file-like object or a :term:`path-like object`.

   .. versionchanged:: 3.2
      Added the ability to use :class:`ZipFile` as a context manager.

   .. versionchanged:: 3.11
      Added support for specifying member name encoding for reading
      metadata in the zipfile's directory and file headers.


.. method:: ZipFile.close()

   Close the archive file.  You must call :meth:`close` before exiting your program
   or essential records will not be written.


.. method:: ZipFile.getinfo(name)

   Return a :class:`ZipInfo` object with information about the archive member
   *name*.  Calling :meth:`getinfo` for a name not currently contained in the
   archive will raise a :exc:`KeyError`.


.. method:: ZipFile.infolist()

   Return a list containing a :class:`ZipInfo` object for each member of the
   archive.  The objects are in the same order as their entries in the actual ZIP
   file on disk if an existing archive was opened.
