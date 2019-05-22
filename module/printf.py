#!/usr/bin/python
# coding:utf8
# Created by wangyikai at 19/04/08

import sys


class Printf:

    def __init__(self):
        pass

    def write_stdout(self, s):
        # only eventlistener protocol messages may be sent to stdout
        sys.stdout.write(s)
        sys.stdout.flush()

    def write_stderr(self, s):
        sys.stderr.write(s)
        sys.stderr.flush()
