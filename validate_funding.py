#!/usr/bin/env python3
"""Back-compat shim: same as `python3 -m devhound check`."""
import sys
from devhound.cli import main

sys.exit(main(["check", *sys.argv[1:]]))
