import sys

from todoapp.taktk import Application

entry = "/"

if len(sys.argv) > 1:
    entry = sys.argv[1]

Application().run(entry)
# Application().redirect_to_singleton(entry)
