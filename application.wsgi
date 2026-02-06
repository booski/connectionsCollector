#!/usr/bin/python3

from os.path import dirname, realpath, abspath
from inspect import getsourcefile
import sys

# Hack to auto-detect the current diectory and add it to the python path
scriptpath = dirname(realpath(abspath(getsourcefile(lambda:0))))
if scriptpath not in sys.path:
    sys.path.insert(0, scriptpath)

from api import app as application
