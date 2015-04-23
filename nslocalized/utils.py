# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

narrow = len('\U00010000') == 2

# This mess is to deal with the fact that:
#
# 1. Python is available in both narrow (UTF-16) and wide (UCS-4) builds.
# 2. Python 3 doesn't support unichr, but uses chr instead.
# 3. unichr() on narrow builds doesn't return surrogate pairs.

try:
    try:
        unichr(0x10000)
    except NameError:
        unichr = chr
        unichr(0x10000)
except ValueError:
    def uchr(x):
        if x < 0x10000:
            return unichr(x)
        else:
            x -= 0x10000
            hi = x >> 10
            lo = x & 0x3ff
            return unichr(0xd800 + hi) + unichr(0xdc00 + lo)
else:
    uchr = unichr

def ord_skip(s, ndx):
    ch = ord(s[ndx])
    if ch >= 0xd800 and ch <= 0xdbff:
        hi = (ch - 0xd800) << 10
        ch2 = ord(s[ndx + 1])
        lo = (ch2 - 0xdc00)
        return (0x10000 + (hi | lo), 2)
    return (ch, 1)

_c_escapes = {
    0x07: 'a',
    0x08: 'b',
    0x0c: 'f',
    0x0a: 'n',
    0x0d: 'r',
    0x09: 't',
    0x0b: 'v',
    0x22: '"',
    0x5c: '\\'
}
if narrow:
    _esc_re = re.compile('([\x00-\x1f\x7f-\x9f\u200e\u200f\u2028-\u202e\ufe00-\ufe0f"\\\\]|\udb40[\udd00-\uddef])')
else:
    _esc_re = re.compile('[\x00-\x1f\x7f-\x9f\u200e\u200f\u2028-\u202e\ufe00-\ufe0f\U000e0100-\U000e01ef"\\\\]')
def escape_string(s):
    result = []
    pos = 0
    end = len(s)
    while pos < end:
        m = _esc_re.search(s, pos)
        if m:
            result.append(s[pos:m.start(0)])
            ch = m.group(0)
            cp = ord_skip(ch, 0)[0]
            pos = m.end(0)

            if cp in _c_escapes:
                result.append('\\%s' % _c_escapes[cp])
            elif cp <= 0xff:
                result.append('\\x%02x' % cp)
            elif cp <= 0xffff:
                result.append('\\u%04x' % cp)
            else:
                result.append('\\U%08x' % cp)
        else:
            result.append(s[pos:])
            pos = end
    return ''.join(result)
