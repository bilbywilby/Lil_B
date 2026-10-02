import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from devhound import brand, funding, hooks, secrets  # noqa: E402
from devhound.cli import main  # noqa: E402
from devhound.sarif import to_sarif  # noqa: E402
from devhound.spdx import unknown_ids  # noqa: E402


def good():
    return json.loads(json.dumps(funding.TEMPLATE))


class FundingTests(unittest.TestCase):
    def rules(self, d, **kw):
        return {f.rule_id for f in funding.validate_data(d, **kw) if f.level == "error"}

    def test_template_passes(self):
        self.assertEqual(self.rules(good()), set())

    def test_repo_funding_passes(self):
        _, f = funding.validate_file(ROOT / "FUNDING.json", strict=True)
        self.assertEqual([x for x in f if x.level == "error"], [])

    def test_sum_must_be_100(self):
        d = good(); d["use_of_funds_breakdown"]["community_support_percentage"] = 21
        self.assertIn("DH-FUND-003", self.rules(d))

    def test_fractional_sum_exact(self):
        d = good(); b = d["use_of_funds_breakdown"]
        b.update(infrastructure_costs_percentage=20.5, developer_compensation_percentage=39.5)
        self.assertEqual(self.rules(d), set())
        b["developer_compensation_percentage"] = 39.4
        self.assertIn("DH-FUND-003", self.rules(d))

    def test_missing_field(self):
        d = good(); del d["use_of_funds_breakdown"]["reserve_and_emergency_percentage"]
        self.assertIn("DH-FUND-002", self.rules(d))

    def test_string_boolean_rejected(self):
        d = good(); d["funding_status"]["seeking_funding"] = "false"
        self.assertIn("DH-FUND-004", self.rules(d))

    def test_int_is_not_boolean(self):
        d = good(); d["funding_status"]["active"] = 1
        self.assertIn("DH-FUND-004", self.rules(d))

    def test_funding_status_must_be_object_of_booleans(self):
        d = good(); d["funding_status"] = "community_supported"
        self.assertIn("DH-FUND-004", self.rules(d))
        d = good(); d["funding_status"]["note"] = "text"
        self.assertIn("DH-FUND-004", self.rules(d))

    def test_top_level_seeking_funding_rejected(self):
        d = good(); d["seeking_funding"] = False
        self.assertIn("DH-FUND-004", self.rules(d))

    def test_nested_boolean_checked(self):
        d = good(); d["privacy"]["telemetry_opt_in"] = "no"
        self.assertIn("DH-FUND-004", self.rules(d))

    def test_bool_in_breakdown_rejected(self):
        d = good(); d["use_of_funds_breakdown"]["community_support_percentage"] = True
        self.assertIn("DH-FUND-003", self.rules(d))

    def test_ask_requires_breakdown(self):
        d = good(); del d["use_of_funds_breakdown"]; d["funding_status"]["seeking_funding"] = True
        self.assertIn("DH-FUND-007", self.rules(d))

    def test_sponsor_tier_reference(self):
        d = good(); d["corporate_sponsorship"] = {"sponsorship_levels": [{"name": "Gold"}],
                                                   "existing_sponsors": [{"company_name": "X", "level": "Platinum"}]}
        self.assertIn("DH-FUND-005", self.rules(d))

    def test_spdx(self):
        self.assertEqual(unknown_ids("MIT OR Apache-2.0"), [])
        self.assertEqual(unknown_ids("GPL-3.0-or-later"), [])
        self.assertEqual(unknown_ids("Made-Up-1.0"), ["Made-Up-1.0"])
        d = good(); d["project"]["license"] = "Made-Up-1.0"
        self.assertEqual(self.rules(d), set())
        self.assertIn("DH-FUND-006", self.rules(d, strict=True))

    def test_bad_json(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t, "FUNDING.json"); p.write_text("{nope")
            data, f = funding.validate_file(p)
            self.assertIsNone(data); self.assertEqual(f[0].rule_id, "DH-FUND-001")


class SecretTests(unittest.TestCase):
    # Fake tokens are assembled at runtime so this file itself never contains one.
    AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
    GH = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
    PEM = "-----BEGIN " + "RSA PRIVATE KEY-----"

    def test_detects_known_tokens(self):
        for tok, rule in [(self.AWS, "DH-SEC-002"), (self.GH, "DH-SEC-003"), (self.PEM, "DH-SEC-005")]:
            f = secrets.scan_text(f"x = {tok}\n", "a.py")
            self.assertEqual([x.rule_id for x in f], [rule], tok[:6])

    def test_values_never_in_output(self):
        f = secrets.scan_text(f'token = "{self.GH}"\n', "a.py")
        blob = json.dumps(to_sarif(f)) + json.dumps([x.__dict__ for x in f])
        self.assertNotIn(self.GH, blob)
        self.assertNotIn(self.GH[:12], blob)

    def test_generic_high_entropy(self):
        f = secrets.scan_text('api_key = "Zx9fQ2mK7pLw4RtY8vB3nC6d"\n', "a.py")
        self.assertEqual([x.rule_id for x in f], ["DH-SEC-001"])

    def test_low_entropy_placeholder_ignored(self):
        self.assertEqual(secrets.scan_text('password = "aaaaaaaaaaaaaaaaaaaa"\n', "a.py"), [])
        self.assertEqual(secrets.scan_text('token = os.environ["TOKEN"]\n', "a.py"), [])

    def test_inline_ignore(self):
        self.assertEqual(secrets.scan_text(f"x = {self.AWS}  # devhound:ignore\n", "a.py"), [])

    def test_scan_paths_skips_binary_and_ignored(self):
        with tempfile.TemporaryDirectory() as t:
            Path(t, "a.txt").write_text(f"k={self.AWS}\n")
            Path(t, "b.bin").write_bytes(b"\0" + self.AWS.encode())
            Path(t, "skip").mkdir(); Path(t, "skip", "c.txt").write_text(self.AWS)
            Path(t, ".devhoundignore").write_text("skip/\n")
            f, n = secrets.scan_paths([t], root=t)
            self.assertEqual([x.path for x in f], ["a.txt"]); self.assertEqual(n, 2)  # a.txt + .devhoundignore

    def test_repo_is_clean(self):
        f, n = secrets.scan_paths([str(ROOT)], root=str(ROOT))
        self.assertGreater(n, 10, "scanner must walk directories; scanning 0 files would be a silent false-clean")
        self.assertEqual([(x.path, x.line, x.rule_id) for x in f], [])


class SarifTests(unittest.TestCase):
    def test_shape(self):
        f = secrets.scan_text("k = " + SecretTests.AWS + "\n", "src/config.ts")
        s = to_sarif(f)
        self.assertEqual(s["version"], "2.1.0")
        r = s["runs"][0]["results"][0]
        self.assertEqual(r["locations"][0]["physicalLocation"]["region"]["startLine"], 1)
        self.assertEqual(s["runs"][0]["tool"]["driver"]["name"], "DevHound Sniffer")


class GitTests(unittest.TestCase):
    """Hermetic: ignores the developer's global git config (hooksPath, templateDir, identity)."""

    ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

    @classmethod
    def setUpClass(cls):
        cls._saved = {k: os.environ.get(k) for k in cls.ENV}
        os.environ.update(cls.ENV)

    @classmethod
    def tearDownClass(cls):
        for k, v in cls._saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d = Path(self.t.name)
        self.git("init", "-q", "--template=")
        self.git("config", "user.email", "t@example.com"); self.git("config", "user.name", "t")

    def tearDown(self):
        self.t.cleanup()

    def git(self, *a):
        return subprocess.run(["git", *a], cwd=self.d, capture_output=True, text=True)

    def test_hooks_install_uninstall_preserve_foreign(self):
        hd = self.d / ".git" / "hooks"; hd.mkdir(exist_ok=True)
        (hd / "pre-commit").write_text("#!/bin/sh\necho mine\n")
        msgs = hooks.install(self.d)
        self.assertIn("skip", [k for k, _ in msgs])
        self.assertIn("mine", (hd / "pre-commit").read_text())
        self.assertIn(hooks.MARKER, (hd / "pre-push").read_text())
        hooks.install(self.d, force=True)
        self.assertIn(hooks.MARKER, (hd / "pre-commit").read_text())
        hooks.uninstall(self.d)
        self.assertIn("mine", (hd / "pre-commit").read_text())
        self.assertFalse((hd / "pre-push").exists())

    def test_shared_hooks_path_is_not_touched_by_default(self):
        shared = Path(self.t.name, "shared-hooks"); shared.mkdir()
        self.git("config", "core.hooksPath", str(shared))
        msgs = hooks.install(self.d)
        self.assertEqual(list(shared.iterdir()), [])
        self.assertIn("EVERY repo", msgs[0][1])
        hooks.install(self.d, allow_shared=True)
        self.assertTrue((shared / "pre-commit").exists())

    def test_staged_scan_uses_index_not_worktree(self):
        f = self.d / "a.txt"
        f.write_text("k=" + SecretTests.AWS + "\n"); self.git("add", "a.txt")
        f.write_text("clean\n")  # worktree cleaned, but the staged blob is what gets committed
        found, n = secrets.scan_staged(self.d)
        self.assertEqual(n, 1); self.assertEqual([x.rule_id for x in found], ["DH-SEC-002"])

    def test_hook_blocks_commit_end_to_end(self):
        bindir = tempfile.TemporaryDirectory()
        shim = Path(bindir.name, "devhound")
        shim.write_text(f"#!/bin/sh\nPYTHONPATH={ROOT} exec {sys.executable} -m devhound \"$@\"\n"); shim.chmod(0o755)
        env = {**os.environ, "PATH": bindir.name + os.pathsep + os.environ["PATH"]}
        hooks.install(self.d)
        (self.d / "a.txt").write_text("k=" + SecretTests.AWS + "\n"); self.git("add", "a.txt")
        r = subprocess.run(["git", "commit", "-m", "x"], cwd=self.d, capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(SecretTests.AWS, r.stdout + r.stderr)
        (self.d / "a.txt").write_text("hello\n"); self.git("add", "a.txt")
        r = subprocess.run(["git", "commit", "-m", "ok"], cwd=self.d, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        bindir.cleanup()


class BrandTests(unittest.TestCase):
    def test_repo_brand_ok(self):
        self.assertEqual([f for f in brand.check(ROOT) if f.level == "error"], [])

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as t:
            import shutil
            shutil.copytree(ROOT / "assets", Path(t, "assets"))
            svg = Path(t, "assets/logo/husky-primary.svg")
            svg.write_text(svg.read_text().replace("#000000", "#ff0000", 1))
            self.assertIn("DH-BRAND-002", {f.rule_id for f in brand.check(t)})

    def test_splash_is_16x9(self):
        w, h = brand.png_size(ROOT / "assets/logo/splash/devhound-splash-1920x1080.png")
        self.assertEqual((w, h), (1920, 1080))


class PrivacyContractTests(unittest.TestCase):
    FORBIDDEN = re.compile(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|httpx|aiohttp|ftplib|smtplib|telnetlib|ssl|xmlrpc)\b", re.M)

    def test_no_network_imports(self):
        for p in (ROOT / "devhound").glob("*.py"):
            self.assertIsNone(self.FORBIDDEN.search(p.read_text()), f"{p.name} imports a network module")


class CliTests(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(main(["check", str(ROOT / "FUNDING.json")]), 0)
        self.assertEqual(main(["check", "/nonexistent/FUNDING.json"]), 1)
        self.assertEqual(main(["check", "/nonexistent/FUNDING.json", "--if-present"]), 0)
        self.assertEqual(main([]), 2)

    def test_init_writes_valid_template(self):
        with tempfile.TemporaryDirectory() as t:
            p = str(Path(t, "FUNDING.json"))
            self.assertEqual(main(["init", p]), 0)
            self.assertEqual(main(["check", p, "--strict"]), 0)
            self.assertEqual(main(["init", p]), 2)


if __name__ == "__main__":
    unittest.main()
