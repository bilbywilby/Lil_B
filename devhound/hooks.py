"""husky-guard: install/remove DevHound-managed git hooks safely.

Hooks fail open (skip with a notice) if `devhound` is not on PATH, so a missing
install never blocks your work. Bypass any time with `git commit --no-verify`.
"""
import os
import stat
import subprocess
from pathlib import Path

MARKER = "# devhound-managed hook"
HOOKS = {
    "pre-commit": "devhound scan --staged",
    "pre-push": "devhound check --if-present",
}


def _script(cmd):
    return f"""#!/bin/sh
{MARKER}
if ! command -v devhound >/dev/null 2>&1; then
  echo "devhound not found on PATH; skipping check (install it or run: devhound hooks uninstall)" >&2
  exit 0
fi
exec {cmd}
"""


def hooks_dir(root="."):
    out = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=root, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    p = Path(out.stdout.strip())
    return p if p.is_absolute() else Path(root) / p


def shared_hooks_path(root="."):
    """Return core.hooksPath if set (global or local). Such a directory is shared across repos."""
    out = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=root, capture_output=True, text=True)
    return out.stdout.strip() or None if out.returncode == 0 else None


def install(root=".", force=False, allow_shared=False):
    d = hooks_dir(root)
    if d is None:
        return [("error", "Not inside a git repository.")]
    shared = shared_hooks_path(root)
    if shared and not allow_shared:
        return [("skip", f"core.hooksPath is set ({shared}). Hooks there apply to EVERY repo that uses it, so nothing was written."),
                ("note", "Re-run with --shared to install there anyway, or add `devhound scan --staged` to your existing hook.")]
    d.mkdir(parents=True, exist_ok=True)
    msgs = []
    for name, cmd in HOOKS.items():
        target = d / name
        if target.exists() and MARKER not in target.read_text(errors="replace"):
            if not force:
                msgs.append(("skip", f"{name}: existing non-DevHound hook left untouched (use --force to back it up and replace)."))
                continue
            target.rename(target.with_name(name + ".devhound-backup"))
            msgs.append(("note", f"{name}: previous hook saved as {name}.devhound-backup"))
        target.write_text(_script(cmd))
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        msgs.append(("ok", f"{name}: installed ({cmd})"))
    return msgs


def uninstall(root="."):
    d = hooks_dir(root)
    if d is None:
        return [("error", "Not inside a git repository.")]
    msgs = []
    for name in HOOKS:
        t = d / name
        if t.exists() and MARKER in t.read_text(errors="replace"):
            t.unlink()
            bak = d / (name + ".devhound-backup")
            if bak.exists():
                bak.rename(t)
                msgs.append(("ok", f"{name}: removed, previous hook restored"))
            else:
                msgs.append(("ok", f"{name}: removed"))
        else:
            msgs.append(("skip", f"{name}: no DevHound hook present"))
    return msgs


def status(root="."):
    d = hooks_dir(root)
    if d is None:
        return [("error", "Not inside a git repository.")]
    return [("ok" if (d / n).exists() and MARKER in (d / n).read_text(errors="replace") else "skip",
             f"{n}: {'installed' if (d / n).exists() and MARKER in (d / n).read_text(errors='replace') else 'not installed'}")
            for n in HOOKS]
