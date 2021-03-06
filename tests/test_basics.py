# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import io
from nslocalized import *

def test_read_utf8_no_bom():
    """Test that we can read UTF-8 strings files."""
    data='''\
/* Test string */
"åéîøü" = "ÅÉÎØÜ";
'''.encode('utf-8')
    
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

def test_raw_keys():
    """Test that unquoted keys are parsed properly."""
    text = '''\
/* Name of the app. */
CFBundleDisplayName = "My Cool App";
NSPhotoLibraryUsageDescription = "Sharing photos is fun!";
'''
    with io.BytesIO(text.encode('utf_8')) as f:
        st = StringTable.read(f)
    assert st['CFBundleDisplayName'] == 'My Cool App'
    assert st.lookup('CFBundleDisplayName').comment == 'Name of the app.'
    assert st['NSPhotoLibraryUsageDescription'] == 'Sharing photos is fun!'
    assert st.lookup('NSPhotoLibraryUsageDescription').comment is None

def test_include_empty_comments():
    """Test writing and not writing empty comments."""
    text = '''\
"A" = "A";
'''

    text_with_empty_comments = '''\
/* No description */
"A" = "A";
'''
    with io.BytesIO(text.encode('utf_8')) as f:
        st = StringTable.read(f)

    with io.BytesIO() as f:
        st.write(f, encoding='utf-8')
        f.seek(0)
        text2 = f.read().decode('utf-8')
        assert text == text2

    with io.BytesIO() as f:
        st.include_empty_comments = True
        st.write(f, encoding='utf-8')
        f.seek(0)
        text2 = f.read().decode('utf-8')
        assert text_with_empty_comments == text2

def test_comments():
    """Test that comments are parsed properly."""
    text = '''\
/* This is a C-style comment which goes over
   multiple lines */
"A" = "A";

/* This is a C-style comment with a
/* nested start
   comment */
"B" = "B";

/* This is a C-style comment with what looks like a key inside
"NotAKey" = "NotAValue";
*/
"C" = "C";

// This is a C++-style comment
"D" = "D";

// This C++-style comment goes over
// multiple lines
"E" = "E";

"ThisHasNoComment" = "NoComment";
'''
    with io.BytesIO(text.encode('utf_8')) as f:
        st = StringTable.read(f)
    assert st['A'] == 'A'
    assert st.lookup('A').comment == 'This is a C-style comment which goes over multiple lines'
    assert st['B'] == 'B'
    assert st.lookup('B').comment == 'This is a C-style comment with a /* nested start comment'
    assert st['C'] == 'C'
    assert st.lookup('C').comment == 'This is a C-style comment with what looks like a key inside "NotAKey" = "NotAValue";'
    assert st['D'] == 'D'
    assert st.lookup('D').comment == 'This is a C++-style comment'
    assert st['E'] == 'E'
    assert st.lookup('E').comment == 'This C++-style comment goes over multiple lines'
    assert st['ThisHasNoComment'] == 'NoComment'
    assert st.lookup('ThisHasNoComment').comment is None
