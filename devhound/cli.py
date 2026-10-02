"""devhound command line interface. Offline by design; see PRIVACY.md."""
import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, brand, funding, hooks, mascot, secrets
from .sarif import to_sarif

EXIT_OK, EXIT_FINDINGS, EXIT_USAGE = 0, 1, 2


def _color():
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _color() else s


def _emit(findings, fmt, output, summary):
    if fmt == "sarif":
        text = json.dumps(to_sarif(findings), indent=2) + "\n"
    elif fmt == "json":
        text = json.dumps([f.__dict__ for f in findings], indent=2) + "\n"
    else:
        lines = []
        for f in findings:
            loc = f"{f.path}:{f.line or 1}:{f.column or 1}"
            lines.append(f"{loc}: {f.level}: {f.message} [{f.rule_id}]")
            if f.fix:
                lines.append(f"    fix: {f.fix}")
        text = "\n".join(lines) + ("\n" if lines else "")
    if output:
        Path(output).write_text(text)
    else:
        sys.stdout.write(text)
    errs = sum(f.level == "error" for f in findings)
    warns = sum(f.level == "warning" for f in findings)
    if errs:
        tag = _c("31;1", "FAIL")
    elif warns:
        tag = _c("33;1", "WARN")
    else:
        tag = _c("32;1", "OK")
    print(f"{tag} {summary} ({errs} error(s), {warns} warning(s))", file=sys.stderr)
    return EXIT_FINDINGS if errs else EXIT_OK


def cmd_check(a):
    p = Path(a.file)
    if a.if_present and not p.exists():
        print("OK no FUNDING.json present; nothing to check", file=sys.stderr)
        return EXIT_OK
    _, findings = funding.validate_file(p, a.strict)
    return _emit(findings, a.format, a.output, f"checked {p}")


def cmd_scan(a):
    if a.staged:
        findings, n = secrets.scan_staged()
        if findings is None:
            print("error: --staged needs a git repository with git installed", file=sys.stderr)
            return EXIT_USAGE
    else:
        findings, n = secrets.scan_paths(a.paths or ["."])
    code = _emit(findings, a.format, a.output, f"scanned {n} file(s) locally")
    if code and a.staged:
        print("Commit blocked. Fix the findings, mark a false positive with `devhound:ignore` on that line,\n"
              "or bypass once with `git commit --no-verify`.", file=sys.stderr)
    return code


def cmd_brand(a):
    if a.update_checksums:
        brand.write_checksums()
        print("Updated assets/logo/CHECKSUMS.sha256", file=sys.stderr)
    return _emit(brand.check(), a.format, a.output, "checked brand assets")


def cmd_hooks(a):
    fn = {"install": lambda: hooks.install(force=a.force, allow_shared=a.shared), "uninstall": hooks.uninstall, "status": hooks.status}[a.action]
    msgs = fn()
    icons = {"ok": "✓", "skip": "-", "note": "i", "error": "✗"}
    for kind, m in msgs:
        print(f"{icons[kind]} {m}")
    return EXIT_USAGE if any(k == "error" for k, _ in msgs) else EXIT_OK


def cmd_init(a):
    p = Path(a.file)
    if p.exists():
        print(f"{p} already exists; not overwriting.", file=sys.stderr)
        return EXIT_USAGE
    p.write_text(json.dumps(funding.TEMPLATE, indent=2) + "\n")
    print(f"Created {p}. Edit the percentages (they must total 100), then run `devhound check`.")
    return EXIT_OK


def cmd_doctor(a):
    print(f"devhound {__version__}")
    print("network access : none (this tool never connects to the internet)")
    print("telemetry      : none")
    print("secret output  : values are never printed or stored")
    print("git            :", "found" if any(os.access(os.path.join(d, "git"), os.X_OK) for d in os.environ.get("PATH", "").split(os.pathsep)) else "not found (hooks/--staged unavailable)")
    return EXIT_OK


def build_parser():
    p = argparse.ArgumentParser(prog="devhound", description="Offline, privacy-first repo checks for DevHound projects.")
    p.add_argument("--version", action="version", version=f"devhound {__version__}")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    def common(sp):
        sp.add_argument("--format", choices=["text", "json", "sarif"], default="text")
        sp.add_argument("--output", "-o", help="write results to a file instead of stdout")

    s = sub.add_parser("check", help="validate FUNDING.json (percentages total 100, real booleans, SPDX)")
    s.add_argument("file", nargs="?", default="FUNDING.json")
    s.add_argument("--strict", action="store_true")
    s.add_argument("--if-present", action="store_true", help="succeed quietly when the file does not exist")
    common(s)
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("scan", help="scan for hardcoded secrets locally (values are never printed)")
    s.add_argument("paths", nargs="*")
    s.add_argument("--staged", action="store_true", help="scan staged git content only")
    common(s)
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser("brand", help="verify brand assets and official-mark checksums")
    s.add_argument("--update-checksums", action="store_true")
    common(s)
    s.set_defaults(fn=cmd_brand)

    s = sub.add_parser("hooks", help="install/remove git hooks (husky-guard)")
    s.add_argument("action", choices=["install", "uninstall", "status"])
    s.add_argument("--force", action="store_true", help="back up and replace existing hooks")
    s.add_argument("--shared", action="store_true", help="allow installing into a shared core.hooksPath directory")
    s.set_defaults(fn=cmd_hooks)

    s = sub.add_parser("init", help="create a starter FUNDING.json")
    s.add_argument("file", nargs="?", default="FUNDING.json")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("doctor", help="show privacy guarantees and environment")
    s.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("mascot", help="print the DevHound husky")
    s.set_defaults(fn=lambda a: print(mascot.render()) or EXIT_OK)
    return p


def main(argv=None):
    parser = build_parser()
    a = parser.parse_args(argv)
    if not getattr(a, "fn", None):
        parser.print_help()
        return EXIT_USAGE
    try:
        return a.fn(a)
    except BrokenPipeError:  # e.g. `devhound scan | head`
        try:
            sys.stdout.close()
        except Exception:
            pass
        return EXIT_OK
