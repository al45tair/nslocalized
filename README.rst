nslocalized
===========

What is this?
-------------

It’s a package of Python code for manipulating Mac OS X/iOS .strings files,
which has been written carefully to support all of the character escapes and
Unicode characters you might wish to use.

How do I use it?
----------------

To read a .strings file::

  >>> from nslocalized import StringTable
  >>> st = StringTable.read('/path/to/my/Localized.strings')

or to read the strings into an existing ``StringTable``::

  >>> st.read('/path/to/my/other/Localized.strings')

To write a new .strings file::

  >>> st.write('/path/to/my/new/Localized.strings')

By default, that uses host-endian UTF-16, but you can specify the encoding::

  >>> st.write('/path/to/my/new/Localized.strings', encoding='utf_8')

Each string is represented by a ``LocalizedString`` object; given the strings
file::

  /* My important string */
  "Very important" = "Très important";

in a ``StringTable`` ``st``::

  >>> ls = st.lookup('Very important')
  >>> print ls.source
  Very important
  >>> print ls.target
  Très important
  >>> print ls.comment
  My important string

You can also add entries to a ``StringTable`` with::

  >>> st.store(LocalizedString('One', 'Uno'))

or with a comment::

  >>> st.store(LocalizedString('MB', 'Mo', 'Megabytes'))

Finally, for simple access you can use the ``[]`` operator::

  >>> st['GB'] = 'Go'
  >>> print st['MB']
  Mo
