# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import io
from nslocalized import *

def test_read_utf8_no_bom():
    """Test that we can read UTF-8 strings files."""
    data=b'''\
/* Test string */
"åéîøü" = "ÅÉÎØÜ";
'''
    
    with io.BytesIO(data) as f:
        st = StringTable.read(f)

    assert st['åéîøü'] == 'ÅÉÎØÜ'
    assert st.lookup('åéîøü').comment == 'Test string'

def test_read_encodings():
    """Test that we can read UTF-8 and UTF-16 strings files."""
    text = '''\ufeff\
/* Test string */
"åéîøü" = "ÅÉÎØÜ";
'''
    for encoding in ['utf_8', 'utf_16_be', 'utf_16_le']:
        data = text.encode(encoding)

        with io.BytesIO(data) as f:
            st = StringTable.read(f)

        assert st['åéîøü'] == 'ÅÉÎØÜ'
        assert st.lookup('åéîøü').comment == 'Test string'

def test_escapes():
    """Test that we can read escaped strings properly."""
    text = '''\
/* C escapes */
"\\a\\b\\f\\n\\r\\t\\v" = "abfnrtv";

/* Octal escapes */
"\\101" = "A";

/* Hex escapes */
"\\x42" = "B";

/* BMP escapes */
"\\u2030" = "PER MILLE";

/* Full Unicode escapes */
"\\U0001f600" = "GRINNING FACE";

/* Quotes */
"This is \\"quoted\\" text." = "This is “quoted” text.";

/* Backslashes and others */
"This \\\\ is a backslash.  This \\* is an asterisk." = "Backslash test";
'''

    with io.BytesIO(text.encode('utf_8')) as f:
        st = StringTable.read(f)
    
    assert st['\a\b\f\n\r\t\v'] == 'abfnrtv'
    assert st['A'] == 'A'
    assert st['B'] == 'B'
    assert st['‰'] == 'PER MILLE'
    assert st['\U0001f600'] == 'GRINNING FACE'
    assert st['This is "quoted" text.'] == "This is “quoted” text."
    assert st['This \\ is a backslash.  This * is an asterisk.'] == "Backslash test"

def test_writing():
    """Test that we can write strings files."""
    text='''\ufeff\
/* Try some accents åéîøü */
"åéîøü" = "ÅÉÎØÜ";

/* And some escapes */
"\\a\\b\\f\\n\\r\\t\\v" = "\\101 \\x42 \\u2030 \\U0001f600";

/* And some more escapes */
"\x03\u200e\u202a\ufe05\U000e0101" = "\\" \\' \\*";
'''

    with io.BytesIO(text.encode('utf_16_be')) as f:
        st = StringTable.read(f)

    # We do this by testing that we can round-trip; note that some of the escaped
    # things above will be un-escaped(!)
    for encoding in ['utf_8', 'utf_16_be', 'utf_16_le']:
        with io.BytesIO() as f:
            st.write(f, encoding=encoding)
            f.seek(0)
            s2 = StringTable.read(f)

            assert st == s2
