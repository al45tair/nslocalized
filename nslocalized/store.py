# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import io
import re

from .utils import uchr, escape_string

# Read states
EXPECTING_ITEM = 0
IN_COMMENT = 1
EXPECTING_KEY = 2
IN_KEY = 3
EXPECTING_EQUALS = 4
EXPECTING_TARGET = 5
IN_TARGET = 6
EXPECTING_SEMICOLON = 7

_c_escapes = {
    'a': '\x07',
    'b': '\x08',
    'f': '\x0c',
    'n': '\x0a',
    'r': '\x0d',
    't': '\x09',
    'v': '\x0b'
}
    
_start_re = re.compile(r'\s*(?:/\*|")')
_comment_re = re.compile(r'\*/')
_exp_key_re = re.compile(r'\s*"')
_key_re = re.compile(r'(?:\\|")')
_hex_re = re.compile(r'[A-Fa-f0-9]+')
_oct_re = re.compile(r'[0-7]{1,3}')
_u4_re = re.compile(r'[A-Fa-f0-9]{4}')
_u8_re = re.compile(r'[A-Fa-f0-9]{8}')
_equals_re = re.compile(r'\s*=\s*')
_semi_re = re.compile(r'\s*;\s*')

class alsoconstruct(object):
    def __init__(self, method):
        self.method = method

    def __get__(self, obj=None, klass=None):
        if obj is None:
            obj = klass()
        return lambda *args: self.method(obj, *args)

class LocalizedString(object):
    __slots__ = ['source', 'target', 'comment']
    
    def __init__(self, source, target, comment=None):
        # The string to translate
        self.source = source

        # The translated string
        self.target = target

        # The comment, if any
        self.comment = comment

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target and self.comment == other.comment

    def __ne__(self, other):
        return self.source != other.source or self.target != other.target or self.comment != other.comment
        
    def __repr__(self):
        return '%r' % self.target
    
class StringTable(object):
    def __init__(self):
        self.strings = {}

    def __eq__(self, other):
        return self.strings == other.strings

    def __ne__(self, other):
        return self.strings != other.strings
        
    def __getitem__(self, source):
        return self.strings[source].target

    def __setitem__(self, source, target):
        self.store(LocalizedString(source, target))

    def __repr__(self):
        return '%r' % self.strings

    def lookup(self, source):
        return self.strings.get(source, None)

    def store(self, localized_string):
        cur = self.strings.get(localized_string.source, None)
        if cur:
            if localized_string.comment:
                if cur.comment:
                    cur.comment += '\n' + localized_string.comment
                else:
                    cur.comment = localized_string.comment
            cur.target = localized_string.target
        else:
            self.strings[localized_string.source] = localized_string

    # If called as StringTable.read(), will construct a new object and read
    # the strings into that.  Otherwise reads into the stringtable "self".
    @alsoconstruct
    def read(self, file_or_name):
        if isinstance(file_or_name, basestring):
            buffered = io.open(file_or_name, 'rb')
        elif getattr(file_or_name, 'peek', None):
            buffered = file_or_name
        elif getattr(file_or_name, 'readable', None) is None:
            buffered = io.open(file_or_name.fileno(), 'rb')
        else:
            buffered = io.BufferedReader(file_or_name)
        
        maybe_bom = buffered.peek(2)[:2]

        if maybe_bom == b'\xfe\xff':
            encoding = 'utf_16_be'
            buffered.read(2)
        elif maybe_bom == b'\xff\xfe':
            encoding = 'utf_16_le'
            buffered.read(2)
        elif maybe_bom == b'\xef\xbb':
            encoding = 'utf_8'
            buffered.read(3)
        else:
            encoding = 'utf_8'

        reader_factory = codecs.getreader(encoding)

        reader = reader_factory(buffered)

        state = EXPECTING_ITEM
        comment = None
        key = None
        target = None
        skip_nl = True
        chunks = []

        def handle_string(m, pos, state, next_state):
            skip_nl = False
            if m:
                chunks.append(line[pos:m.start(0)])
                if m.group(0) == '"':
                    state = next_state
                    pos = m.end(0)
                    return (state, pos, skip_nl, ''.join(chunks))
                elif m.group(0) == '\\':
                    pos = m.end(0)
                    ch = line[pos]
                    if pos == end:
                        skip_nl = True
                    elif ch in _c_escapes:
                        chunks.append(_c_escapes[ch])
                        pos += 1
                    elif ch in ('x', 'u', 'U'):
                        pos += 1
                        if ch == 'x':
                            hm = _hex_re.match(line, pos)
                        elif ch == 'u':
                            hm = _u4_re.match(line, pos)
                        elif ch == 'U':
                            hm = _u8_re.match(line, pos)
                        if hm:
                            cp = int(hm.group(0), 16)
                            if cp >= 0xd800 and cp <= 0xdfff or cp > 0x10ffff:
                                raise ValueError('Bad Unicode escape')
                            chunks.append(uchr(cp))
                            pos = hm.end(0)
                        else:
                            chunks.append('x')
                    elif ch >= '0' and ch < '8':
                        hm = _oct_re.match(line, pos)
                        cp = int(hm.group(0), 8)
                        chunks.append(uchr(cp))
                        pos = hm.end(0)
                    else:
                        chunks.append(ch)
                        pos += 1
            else:
                chunks.append(line[pos:])
                pos = end            

            return (state, pos, skip_nl, None)
        
        for line in reader:
            end = len(line)
            pos = 0
            if not skip_nl:
                chunks.append('\n')
                skip_nl = False
            while pos < end:
                if state == EXPECTING_ITEM:
                    m = _start_re.match(line, pos)
                    if m:
                        if m.group(0) == '/*':
                            state = IN_COMMENT
                            chunks = []
                            pos = m.end(0)
                        elif m.group(0) == '"':
                            state = IN_KEY
                            chunks = []
                            pos = m.end(0)
                    elif line.strip() != '':
                        raise ValueError('Unexpected garbage in input')
                    else:
                        pos = end
                elif state == IN_COMMENT:
                    m = _comment_re.search(line, pos)
                    if m:
                        state = EXPECTING_KEY
                        chunks.append(line[pos:m.start(0)].strip())
                        comment = ''.join(chunks)
                    else:
                        chunks.append(line[pos:].strip())
                        pos = end
                elif state == EXPECTING_KEY:
                    m = _exp_key_re.match(line, pos)
                    if m:
                        state = IN_KEY
                        chunks = []
                        pos = m.end(0)
                    else:
                        pos = end
                elif state == IN_KEY:
                    state, pos, skip_nl, key \
                      = handle_string(_key_re.search(line, pos),
                                      pos, state, EXPECTING_EQUALS)
                elif state == EXPECTING_EQUALS:
                    m = _equals_re.match(line, pos)
                    if m:
                        state = EXPECTING_TARGET
                        pos = m.end(0)
                    elif line.strip() != '':
                        raise ValueError('Missing equals')
                elif state == EXPECTING_TARGET:
                    m = _exp_key_re.match(line, pos)
                    if m:
                        state = IN_TARGET
                        chunks = []
                        pos = m.end(0)
                    else:
                        pos = end
                elif state == IN_TARGET:
                    state, pos, skip_nl, target \
                      = handle_string(_key_re.search(line, pos),
                                      pos, state, EXPECTING_SEMICOLON)
                elif state == EXPECTING_SEMICOLON:
                    m = _semi_re.match(line, pos)
                    if m:
                        state = EXPECTING_ITEM
                        self.store(LocalizedString(key, target, comment))
                        pos = m.end(0)
                        key = None
                        target = None
                        comment = None
                    elif line.strip() != '':
                        raise ValueError('Missing semicolon')
                    
        if state != EXPECTING_ITEM:
            raise ValueError('Bad strings file')

        return self;
        
    def write(self, file_or_name, encoding='utf_16'):
        if isinstance(file_or_name, basestring):
            file_or_name = io.open(file_or_name, 'wb')

        writer_factory = codecs.getwriter(encoding)

        writer = writer_factory(file_or_name)

        if encoding != 'utf_8':
            writer.write('\ufeff')
        
        keys = self.strings.keys()
        keys.sort()

        first = True
        for k in keys:
            if first:
                first = False
            else:
                writer.write('\n')
            ls = self.strings[k]
            if ls.comment:
                writer.write('/* %s */\n' % ls.comment)
            else:
                writer.write('/* No description */\n')
            writer.write('"%s" = "%s";\n'
                         % (escape_string(ls.source),
                            escape_string(ls.target)))
