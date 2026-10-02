"""Brand asset integrity checks: presence, validity, sizes, official-mark checksums."""
import hashlib
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

from .findings import Finding

REQUIRED = [
    "assets/logo/husky-primary.svg", "assets/logo/husky-dark-mode.svg",
    "assets/logo/husky-primary.png", "assets/logo/og-card.png",
    "assets/logo/favicons/favicon-32x32.png", "assets/logo/icons/app-icon-1024.png",
    "assets/logo/splash/devhound-splash-1920x1080.png",
]
PROTECTED = ["assets/logo/husky-primary.svg", "assets/logo/husky-dark-mode.svg"]
CHECKSUMS = "assets/logo/CHECKSUMS.sha256"
MAX_SVG = 250 * 1024


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_checksums(root="."):
    root = Path(root)
    lines = [f"{_sha(root / p)}  {p}" for p in PROTECTED]
    (root / CHECKSUMS).write_text("\n".join(lines) + "\n")


def check(root="."):
    root = Path(root)
    f = []
    for rel in REQUIRED:
        p = root / rel
        if not p.is_file():
            f.append(Finding("DH-BRAND-001", "error", f"Required brand asset missing: {rel}", rel,
                             fix="Run `python3 scripts/render.py` to regenerate derived assets."))
            continue
        if rel.endswith(".svg"):
            if p.stat().st_size > MAX_SVG:
                f.append(Finding("DH-BRAND-002", "error", f"{rel} exceeds 250 KB.", rel))
            try:
                ET.parse(p)
            except ET.ParseError as e:
                f.append(Finding("DH-BRAND-002", "error", f"{rel} is not valid XML: {e}", rel))
        elif rel.endswith(".png"):
            size = png_size(p)
            if size is None:
                f.append(Finding("DH-BRAND-002", "error", f"{rel} is not a valid PNG.", rel))
            elif "splash-1920x1080" in rel and (size[0] * 9 != size[1] * 16 or size[0] < 1920):
                f.append(Finding("DH-BRAND-002", "error", f"{rel} must be 16:9 and at least 1920x1080, found {size[0]}x{size[1]}.", rel))
    cs = root / CHECKSUMS
    if not cs.is_file():
        f.append(Finding("DH-BRAND-001", "warning", f"{CHECKSUMS} missing; official-mark integrity not verified.", CHECKSUMS,
                         fix="Run `devhound brand --update-checksums` after confirming the logo is correct."))
    else:
        for line in cs.read_text().splitlines():
            if not line.strip():
                continue
            digest, rel = line.split(None, 1)
            rel = rel.strip()
            if (root / rel).is_file() and _sha(root / rel) != digest:
                f.append(Finding("DH-BRAND-002", "error", f"{rel} differs from the recorded official mark.", rel,
                                 fix="If this is an intentional logo update, run `devhound brand --update-checksums` and note it in CHANGELOG.md."))
    return f
