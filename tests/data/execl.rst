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
