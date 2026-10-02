"""Offline SPDX identifier check against a bundled list of common licenses.

The list is a subset on purpose (no network lookups). Unknown IDs produce a
warning, or an error with --strict, never a silent pass.
"""
import re

COMMON = {
    "0BSD", "AGPL-3.0-only", "AGPL-3.0-or-later", "Apache-2.0", "Artistic-2.0",
    "BSD-2-Clause", "BSD-3-Clause", "BSL-1.0", "CC-BY-4.0", "CC-BY-SA-4.0",
    "CC0-1.0", "EPL-1.0", "EPL-2.0", "EUPL-1.2", "GPL-2.0-only",
    "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later", "ISC",
    "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "MIT", "MIT-0", "MPL-2.0", "MS-PL", "OFL-1.1", "PostgreSQL", "Unlicense",
    "WTFPL", "Zlib",
}

_TOKEN = re.compile(r"[A-Za-z0-9.\-]+\+?")
_OPS = {"AND", "OR", "WITH"}


def unknown_ids(expression):
    """Return identifiers in an SPDX expression that are not in the bundled list."""
    bad = []
    for tok in _TOKEN.findall(expression or ""):
        if tok in _OPS:
            continue
        base = tok[:-1] if tok.endswith("+") else tok
        if base not in COMMON:
            bad.append(tok)
    return bad
