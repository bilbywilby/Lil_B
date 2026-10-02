"""Local secret detection. Findings never include the secret value."""
import fnmatch
import hashlib
import math
import os
import re
import subprocess
from pathlib import Path

from .findings import Finding

PATTERNS = [
    ("DH-SEC-002", "AWS access key ID", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("DH-SEC-003", "GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("DH-SEC-004", "Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("DH-SEC-005", "Private key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("DH-SEC-006", "Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("DH-SEC-007", "Stripe live key", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{20,}\b")),
    ("DH-SEC-008", "DevHound personal access token", re.compile(r"\bdh_pat_[A-Za-z0-9]{24,}\b")),
]
GENERIC = re.compile(
    r"""(?ix)\b(?:api[_-]?key|secret|token|passw(?:or)?d|auth)\w*\s*[:=]\s*["']([^"'\s]{16,})["']"""
)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".mypy_cache"}
MAX_BYTES = 1_000_000
INLINE_IGNORE = "devhound:ignore"


def _entropy(s):
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def _fingerprint(rule, path, line):
    return hashlib.sha256(f"{rule}:{path}:{line}".encode()).hexdigest()[:16]


def scan_text(text, path):
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if INLINE_IGNORE in line:
            continue
        hit_cols = []
        for rule, name, rx in PATTERNS:
            m = rx.search(line)
            if m:
                hit_cols.append(m.start())
                findings.append(Finding(rule, "error", f"{name} detected (value hidden).", path, lineno, m.start() + 1,
                                        "Revoke it, remove it from history, and load it from an environment variable.",
                                        _fingerprint(rule, path, lineno)))
        g = GENERIC.search(line)
        if g and g.start() not in hit_cols and _entropy(g.group(1)) >= 3.5:
            findings.append(Finding("DH-SEC-001", "error", "Hardcoded secret-like value assigned (value hidden).", path, lineno,
                                    g.start() + 1, "Move it to an environment variable or a secret store.",
                                    _fingerprint("DH-SEC-001", path, lineno)))
    return findings


def _load_ignores(root):
    f = Path(root) / ".devhoundignore"
    if not f.exists():
        return []
    return [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]


def _ignored(rel, patterns):
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel, p.rstrip("/") + "/*") or rel.startswith(p.rstrip("/") + "/")
               for p in patterns)


def _looks_binary(b):
    return b"\0" in b[:4096]


def _iter_files(paths):
    for base in paths:
        base = Path(base)
        if base.is_file():
            yield base
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                yield Path(dirpath) / name


def scan_paths(paths, root="."):
    patterns = _load_ignores(root)
    findings, scanned = [], 0
    for fp in _iter_files(paths):
        rel = os.path.relpath(fp, root).replace(os.sep, "/")
        if _ignored(rel, patterns):
            continue
        try:
            if fp.stat().st_size > MAX_BYTES:
                continue
            raw = fp.read_bytes()
        except OSError:
            continue
        if _looks_binary(raw):
            continue
        scanned += 1
        findings += scan_text(raw.decode("utf-8", "replace"), rel)
    return findings, scanned


def scan_staged(root="."):
    """Scan the staged (index) content, which is what would actually be committed."""
    patterns = _load_ignores(root)
    try:
        names = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"],
                               cwd=root, capture_output=True, check=True).stdout.decode().split("\0")
    except (OSError, subprocess.CalledProcessError):
        return None, 0
    findings, scanned = [], 0
    for rel in filter(None, names):
        if _ignored(rel, patterns):
            continue
        blob = subprocess.run(["git", "show", f":{rel}"], cwd=root, capture_output=True)
        if blob.returncode != 0 or len(blob.stdout) > MAX_BYTES or _looks_binary(blob.stdout):
            continue
        scanned += 1
        findings += scan_text(blob.stdout.decode("utf-8", "replace"), rel)
    return findings, scanned
