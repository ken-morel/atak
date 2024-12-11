#!/usr/bin/env python3
"""Main page."""
from efus.parser import parse_file
from efus.namespace import Namespace

np = Namespace()
code = parse_file("test.efus")
print(code)

comp = code.translate(np)
