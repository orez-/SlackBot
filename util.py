from __future__ import print_function

import collections
import contextlib
import sys


color_stack = collections.deque(['0'])


@contextlib.contextmanager
def hilite(color):
    if sys.stdout.isatty():
        attr = {
            'gray': '30',
            'red': '31',
            'green': '32',
            'yellow': '33',
            'lite blue': '34',
            'purple': '35',
            'cyan': '36',
        }[color]
        print('\x1b[{}m'.format(attr), end='')
        sys.stdout.flush()
        color_stack.append(attr)
        yield
        color_stack.pop()
        print('\x1b[{}m'.format(color_stack[-1]), end='')
        sys.stdout.flush()
    else:  # Can't hilight if it's not a tty.
        yield
