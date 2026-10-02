#!/usr/bin/env python3
"""Apply the DevHound CSS to a Jellyfin server's Branding settings (instead of pasting it by hand).

Privacy and safety:
  * Talks ONLY to the server URL you give (default http://127.0.0.1:8096). Non-local addresses
    are refused unless you pass --allow-remote.
  * The API key is read from $JELLYFIN_API_KEY (or a hidden prompt), never from the command line,
    so it can't end up in shell history or `ps`.
  * `plan` (default) changes nothing. `apply` first saves a backup of the current branding to a
    0600 file; `restore FILE` puts it back. Only CustomCss is changed; your login disclaimer and
    other branding are preserved.
Create an API key in Jellyfin: Dashboard > Advanced > API Keys.

Standard library only. Verified against a mock server that mirrors the documented
/System/Configuration/branding endpoints; not yet against a live Jellyfin server.
"""
import argparse
import getpass
import ipaddress
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS_DIR = HERE.parent.parent / "integrations" / "jellyfin"
ENDPOINT = "/System/Configuration/branding"


def is_local(url):
    host = urllib.parse.urlparse(url).hostname or ""
    if host in ("localhost",) or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


class JellyfinError(Exception):
    pass


def request(base, method, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base.rstrip("/") + ENDPOINT, data=data, method=method)
    req.add_header("X-Emby-Token", token)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise JellyfinError("The server rejected the API key (needs an administrator key from Dashboard > Advanced > API Keys).")
        raise JellyfinError(f"Server returned HTTP {e.code} for {method} {ENDPOINT}.")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise JellyfinError(f"Could not reach {base}: {getattr(e, 'reason', e)}")


def get_token():
    token = os.environ.get("JELLYFIN_API_KEY", "").strip()
    if not token and sys.stdin.isatty():
        token = getpass.getpass("Jellyfin API key (hidden): ").strip()
    if not token:
        raise JellyfinError("Set JELLYFIN_API_KEY (or run in a terminal to be prompted).")
    return token


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("action", nargs="?", default="plan", choices=["plan", "apply", "restore"])
    p.add_argument("backup", nargs="?", help="backup file (for restore)")
    p.add_argument("--url", default="http://127.0.0.1:8096")
    p.add_argument("--monochromic", action="store_true", help="use the variant that loads a base theme from a CDN")
    p.add_argument("--css", help="use this CSS file instead of the bundled one")
    p.add_argument("--allow-remote", action="store_true", help="allow a non-local server address")
    a = p.parse_args(argv)

    try:
        if not is_local(a.url) and not a.allow_remote:
            raise JellyfinError(f"{a.url} is not a local/private address. Use --allow-remote if you really mean it.")
        css_path = Path(a.css) if a.css else CSS_DIR / ("custom-with-monochromic.css" if a.monochromic else "custom.css")
        if a.action != "restore" and not css_path.is_file():
            raise JellyfinError(f"CSS file not found: {css_path}")
        token = get_token()
        current = request(a.url, "GET", token) or {}

        if a.action == "restore":
            if not a.backup:
                raise JellyfinError("Usage: apply_branding.py restore BACKUP_FILE")
            request(a.url, "POST", token, json.loads(Path(a.backup).read_text()))
            print(f"Restored branding from {a.backup}")
            return 0

        css = css_path.read_text(encoding="utf-8")
        old = current.get("CustomCss") or ""
        print(f"Server: {a.url}")
        print(f"CSS file: {css_path.name} ({len(css)} bytes); current custom CSS on server: {len(old)} bytes")
        print("Unchanged:", ", ".join(k for k in current if k != "CustomCss") or "(nothing)")
        if a.action == "plan":
            print("Plan only. Nothing was changed. Run with `apply` to write it.")
            return 0

        backup = Path(f"jellyfin-branding-backup-{time.strftime('%Y%m%d-%H%M%S')}.json")
        fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(current, f, indent=2)
        updated = dict(current)
        updated["CustomCss"] = css
        request(a.url, "POST", token, updated)
        after = request(a.url, "GET", token) or {}
        if after.get("CustomCss") != css:
            raise JellyfinError(f"Server did not keep the CSS. Your previous settings are saved in {backup}.")
        print(f"Applied. Previous branding saved to {backup}. Hard-refresh the web UI to see it.")
        return 0
    except JellyfinError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
