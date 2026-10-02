"""Tests for the add-ins in addons/: privacy invariants, drift guards, and behaviour."""
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import yaml
except ImportError:  # keep the suite stdlib-only on a bare system
    yaml = None

AWS = "AKIA" + "ABCDEFGHIJKLMNOP"


def make_shim(directory):
    shim = Path(directory, "devhound")
    shim.write_text(f'#!/bin/sh\nPYTHONPATH={ROOT} exec {sys.executable} -m devhound "$@"\n')
    shim.chmod(0o755)
    return directory


def env_with_shim(shim_dir, **extra):
    env = {**os.environ, "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}"}
    env.update(extra)
    return env


class BrowserPrivacyTests(unittest.TestCase):
    B = ROOT / "addons" / "browser"

    def setUp(self):
        self.m = json.loads((self.B / "manifest.json").read_text())

    def test_minimal_permissions(self):
        self.assertEqual(sorted(self.m["permissions"]), ["activeTab", "scripting"])
        for forbidden in ("host_permissions", "optional_host_permissions", "content_scripts", "background",
                          "web_accessible_resources", "externally_connectable", "optional_permissions"):
            self.assertNotIn(forbidden, self.m)

    def test_csp_blocks_all_network(self):
        csp = self.m["content_security_policy"]["extension_pages"]
        self.assertIn("connect-src 'none'", csp)
        self.assertIn("default-src 'none'", csp)
        self.assertNotIn("unsafe-eval", csp)
        self.assertNotRegex(csp, r"script-src[^;]*(http|\*|unsafe)")

    def test_no_network_or_injection_apis_in_shipped_js(self):
        bad = re.compile(r"\b(fetch|XMLHttpRequest|WebSocket|sendBeacon|EventSource|importScripts)\b|innerHTML|outerHTML|insertAdjacentHTML|\beval\s*\(|new Function|document\.write|https?://")
        for name in ("popup.js", "scan.js", "popup.html"):
            text = (self.B / name).read_text()
            self.assertIsNone(bad.search(text), f"{name} uses a forbidden API")

    def test_rules_are_generated_from_python_scanner(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/gen_browser_rules.py"), "--check"])
        self.assertEqual(r.returncode, 0, "addons/browser/rules.js is stale: run scripts/gen_browser_rules.py")

    def test_python_scanner_matches_shared_cases(self):
        from devhound import secrets
        cases = json.loads((ROOT / "tests/fixtures/secret_cases.json").read_text())
        for c in cases:
            got = [f.rule_id for f in secrets.scan_text("".join(c["parts"]), "x")]
            self.assertEqual(got, c["expect"], c["name"])


class VSCodeExtensionTests(unittest.TestCase):
    V = ROOT / "addons" / "vscode"

    def test_no_network_modules_or_shell(self):
        text = (self.V / "extension.js").read_text() + (self.V / "lib.js").read_text()
        self.assertIsNone(re.search(r"require\(\s*['\"](https?|net|tls|dgram|dns|http2|node-fetch|axios)['\"]\s*\)", text))
        self.assertIsNone(re.search(r"\bexec\s*\(|\bexecSync\b|shell\s*:\s*true|\bspawnSync\b", text))
        self.assertNotIn("fetch(", text)

    def test_manifest_basics(self):
        pkg = json.loads((self.V / "package.json").read_text())
        self.assertEqual(pkg["main"], "./extension.js")
        self.assertIs(pkg["contributes"]["configuration"]["properties"]["devhound.scanOnSave"]["default"], False)
        cmds = {c["command"] for c in pkg["contributes"]["commands"]}
        self.assertEqual(cmds, {"devhound.scan", "devhound.check", "devhound.brand", "devhound.clear"})


@unittest.skipUnless(shutil.which("node"), "node not installed")
class NodeSuiteTests(unittest.TestCase):
    def test_node_tests_pass(self):
        r = subprocess.run(["node", "--test", "addons/browser/test/scan.test.js", "addons/vscode/test/lib.test.js"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-500:])


# ---------------------------------------------------------------- Jellyfin applier
def load_applier():
    spec = importlib.util.spec_from_file_location("apply_branding", ROOT / "addons/jellyfin/apply_branding.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MockJellyfin:
    def __init__(self, token="good", ignore_posts=False):
        self.token, self.ignore_posts = token, ignore_posts
        self.state = {"LoginDisclaimer": "Legal text", "CustomCss": "/* old */", "SplashscreenEnabled": True}
        self.posts = 0
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _ok(self):
                if self.headers.get("X-Emby-Token") != outer.token:
                    self.send_response(401); self.end_headers(); return False
                return self.path == "/System/Configuration/branding"

            def do_GET(self):
                if self._ok():
                    body = json.dumps(outer.state).encode()
                    self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                data = self.rfile.read(length)
                if self._ok():
                    outer.posts += 1
                    if not outer.ignore_posts:
                        outer.state = json.loads(data)
                    self.send_response(204); self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown(); self.server.server_close()


class JellyfinApplierTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_applier()
        self.srv = MockJellyfin()
        self.cwd = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd(); os.chdir(self.cwd.name)
        self.css = (ROOT / "integrations/jellyfin/custom.css").read_text(encoding="utf-8")

    def tearDown(self):
        os.chdir(self.old_cwd); self.cwd.cleanup(); self.srv.close()

    def run_main(self, args, key="good"):
        out, err = io.StringIO(), io.StringIO()
        env = {"JELLYFIN_API_KEY": key} if key is not None else {}
        with mock.patch.dict(os.environ, env, clear=False), redirect_stdout(out), redirect_stderr(err):
            if key is None:
                os.environ.pop("JELLYFIN_API_KEY", None)
            rc = self.mod.main(args)
        return rc, out.getvalue(), err.getvalue()

    def test_is_local(self):
        for u in ("http://127.0.0.1:8096", "http://192.168.0.189:8096", "http://localhost", "http://tv.local:8096", "http://10.0.0.5"):
            self.assertTrue(self.mod.is_local(u), u)
        for u in ("http://example.com", "https://8.8.8.8", "http://jellyfin.example.org"):
            self.assertFalse(self.mod.is_local(u), u)

    def test_plan_changes_nothing(self):
        rc, out, _ = self.run_main(["--url", self.srv.url])
        self.assertEqual(rc, 0); self.assertIn("Nothing was changed", out)
        self.assertEqual(self.srv.posts, 0); self.assertEqual(self.srv.state["CustomCss"], "/* old */")
        self.assertEqual(list(Path(".").glob("jellyfin-branding-backup-*")), [])

    def test_apply_updates_only_css_and_backs_up(self):
        rc, out, _ = self.run_main(["apply", "--url", self.srv.url])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.srv.state["CustomCss"], self.css)
        self.assertEqual(self.srv.state["LoginDisclaimer"], "Legal text")
        self.assertTrue(self.srv.state["SplashscreenEnabled"])
        (backup,) = Path(".").glob("jellyfin-branding-backup-*.json")
        self.assertEqual(json.loads(backup.read_text())["CustomCss"], "/* old */")
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertNotIn(self.css[:60], out)  # CSS body isn't dumped to the terminal

    def test_restore_round_trip(self):
        self.run_main(["apply", "--url", self.srv.url])
        (backup,) = Path(".").glob("jellyfin-branding-backup-*.json")
        rc, out, _ = self.run_main(["restore", str(backup), "--url", self.srv.url])
        self.assertEqual(rc, 0, out); self.assertEqual(self.srv.state["CustomCss"], "/* old */")

    def test_wrong_key_is_rejected_cleanly(self):
        rc, _, err = self.run_main(["apply", "--url", self.srv.url], key="wrong")
        self.assertEqual(rc, 1); self.assertIn("API key", err)
        self.assertNotIn("wrong", err)
        self.assertEqual(self.srv.state["CustomCss"], "/* old */")

    def test_missing_key(self):
        with mock.patch("sys.stdin.isatty", return_value=False):
            rc, _, err = self.run_main(["--url", self.srv.url], key=None)
        self.assertEqual(rc, 1); self.assertIn("JELLYFIN_API_KEY", err)

    def test_remote_refused_without_flag(self):
        rc, _, err = self.run_main(["--url", "http://example.com"])
        self.assertEqual(rc, 1); self.assertIn("--allow-remote", err)

    def test_key_cannot_be_passed_on_command_line(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            self.mod.main(["--api-key", "secret"])
        self.assertEqual(cm.exception.code, 2)

    def test_server_that_drops_the_write_is_detected(self):
        self.srv.ignore_posts = True
        rc, _, err = self.run_main(["apply", "--url", self.srv.url])
        self.assertEqual(rc, 1); self.assertIn("did not keep", err); self.assertIn("backup", err)

    def test_unreachable_server_message(self):
        rc, _, err = self.run_main(["--url", "http://127.0.0.1:1"])
        self.assertEqual(rc, 1); self.assertIn("Could not reach", err)


# ---------------------------------------------------------------- CI integrations
@unittest.skipUnless(yaml, "PyYAML not installed")
class CITests(unittest.TestCase):
    def setUp(self):
        self.action = yaml.safe_load((ROOT / "action.yml").read_text())
        steps = self.action["runs"]["steps"]
        self.script = next(s["run"] for s in steps if s.get("name") == "Run checks")
        self.shimdir = tempfile.TemporaryDirectory(); make_shim(self.shimdir.name)
        self.repo = tempfile.TemporaryDirectory()
        self.dir = Path(self.repo.name)

    def tearDown(self):
        self.shimdir.cleanup(); self.repo.cleanup()

    def run_action(self, **inputs):
        env = env_with_shim(self.shimdir.name, INPUT_SCAN="true", INPUT_FUNDING="true", INPUT_BRAND="false",
                            INPUT_STRICT="false", INPUT_PATHS=".", INPUT_SARIF="")
        env.update({f"INPUT_{k.upper()}": v for k, v in inputs.items()})
        return subprocess.run(["bash", "-c", self.script], cwd=self.dir, env=env, capture_output=True, text=True)

    def test_action_shape(self):
        self.assertEqual(self.action["runs"]["using"], "composite")
        self.assertEqual(set(self.action["inputs"]), {"scan", "funding", "brand", "strict", "paths", "sarif"})

    def test_inputs_are_not_interpolated_into_the_script(self):
        self.assertNotIn("${{", self.script)

    def test_clean_repo_passes_and_leaky_repo_fails_without_echoing_secret(self):
        (self.dir / "a.txt").write_text("hello\n")
        self.assertEqual(self.run_action().returncode, 0)
        (self.dir / "b.txt").write_text(f"k={AWS}\n")
        r = self.run_action()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(AWS, r.stdout + r.stderr)

    def test_all_checks_run_even_if_one_fails(self):
        (self.dir / "b.txt").write_text(f"k={AWS}\n")
        (self.dir / "FUNDING.json").write_text("{bad")
        r = self.run_action()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DH-SEC-002", r.stdout); self.assertIn("DH-FUND-001", r.stdout)

    def test_sarif_output(self):
        (self.dir / "a.txt").write_text("hello\n")
        self.assertEqual(self.run_action(sarif="out.sarif").returncode, 0)
        self.assertEqual(json.loads((self.dir / "out.sarif").read_text())["version"], "2.1.0")

    def test_malicious_paths_input_does_not_execute(self):
        (self.dir / "a.txt").write_text("hello\n")
        r = self.run_action(paths="a.txt; touch pwned; $(touch pwned2)")
        self.assertFalse((self.dir / "pwned").exists() or (self.dir / "pwned2").exists())

    def test_pre_commit_hook_definitions(self):
        hooks = {h["id"]: h for h in yaml.safe_load((ROOT / ".pre-commit-hooks.yaml").read_text())}
        self.assertEqual(set(hooks), {"devhound-scan", "devhound-funding"})
        self.assertEqual(hooks["devhound-scan"]["entry"], "devhound scan")
        self.assertTrue(re.search(hooks["devhound-funding"]["files"], "FUNDING.json"))
        self.assertFalse(re.search(hooks["devhound-funding"]["files"], "docs/FUNDING.json.bak"))
        (self.dir / "leak.txt").write_text(f"k={AWS}\n")
        r = subprocess.run(["devhound", "scan", "leak.txt"], cwd=self.dir, env=env_with_shim(self.shimdir.name), capture_output=True, text=True)
        self.assertEqual(r.returncode, 1); self.assertNotIn(AWS, r.stdout + r.stderr)


# ---------------------------------------------------------------- Shell integration
class ShellTests(unittest.TestCase):
    SH = ROOT / "addons" / "shell" / "devhound.sh"

    def bash(self, script, cwd=None, shim=None):
        env = env_with_shim(shim) if shim else os.environ.copy()
        return subprocess.run(["bash", "-c", f"source {self.SH}\n{script}"], cwd=cwd, env=env, capture_output=True, text=True)

    def test_is_up_to_date_with_cli(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/gen_completions.py"), "--check"])
        self.assertEqual(r.returncode, 0, "addons/shell/devhound.sh is stale: run scripts/gen_completions.py")

    def test_bash_syntax(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(self.SH)]).returncode, 0)

    def complete(self, *words):
        r = self.bash(f'COMP_WORDS=({" ".join(repr(w) for w in words)}); COMP_CWORD={len(words) - 1}; _devhound; echo "${{COMPREPLY[*]}}"')
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()

    def test_completions(self):
        self.assertEqual(self.complete("devhound", "sc"), ["scan"])
        self.assertIn("--staged", self.complete("devhound", "scan", "--st"))
        self.assertEqual(self.complete("devhound", "scan", "--format", ""), ["text", "json", "sarif"])
        self.assertEqual(self.complete("devhound", "hooks", ""), ["install", "uninstall", "status"])
        self.assertIn("--shared", self.complete("devhound", "hooks", "install", "--sh"))

    def test_dh_pass_and_fail(self):
        shim = tempfile.TemporaryDirectory(); make_shim(shim.name)
        repo = tempfile.TemporaryDirectory()
        try:
            Path(repo.name, "a.txt").write_text("hello\n")
            r = self.bash("dh; echo rc=$?", cwd=repo.name, shim=shim.name)
            self.assertIn("rc=0", r.stdout); self.assertIn("scan", r.stdout)
            Path(repo.name, "b.txt").write_text(f"k={AWS}\n")
            r = self.bash("dh; echo rc=$?", cwd=repo.name, shim=shim.name)
            self.assertIn("rc=1", r.stdout)
            self.assertNotIn(AWS, r.stdout + r.stderr)
        finally:
            shim.cleanup(); repo.cleanup()


if __name__ == "__main__":
    unittest.main()
