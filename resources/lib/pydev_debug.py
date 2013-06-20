#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Debug Module: Used to debug XBMC addons in eclipse

import sys

# Make pydev debugger works for auto reload.
# Note pydevd addon required
try:
    import pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
    pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
except ImportError:
    sys.stderr.write("Error: You must install pydevd addon.")
    sys.exit(1)
