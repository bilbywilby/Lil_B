<p align="center">
  <img src="./assets/logo/husky-primary.svg" alt="DevHound logo: stylized husky head with triangular D-tag collar" width="160"/>
</p>

<h1 align="center">DevHound</h1>

<p align="center">
  Offline, privacy-first checks for your repo: secrets, funding files, and brand assets.<br/>
  <strong>No network. No telemetry. Secret values are never printed.</strong>
</p>

---

## Quick start

Requires Python 3.9+ and nothing else (standard library only).

```bash
git clone git@github.com:bilbywilby/Lil_B.git && cd Lil_B
python3 -m devhound doctor        # shows exactly what this tool does and doesn't do
python3 -m devhound scan .        # find hardcoded secrets locally
python3 -m devhound check         # validate FUNDING.json
python3 -m devhound brand         # verify logo files are intact
```

Install the `devhound` command (works on Android terminals, Termux and proot-Debian too):

```bash
pip install .            # or: pipx install .
devhound hooks install   # block commits that contain secrets
```

## What it does

| Command | What you get |
|---|---|
| `devhound scan [paths]` | Detects AWS/GitHub/Slack/Stripe/Google keys, private keys, and high-entropy secret assignments. Output shows file, line and rule only, never the secret. |
| `devhound scan --staged` | Scans exactly what you're about to commit. |
| `devhound check` | Validates `FUNDING.json`: five fund-use percentages total exactly 100, flags are real JSON booleans, sponsors match defined tiers, license is SPDX. |
| `devhound brand` | Confirms required assets exist, SVGs are valid, the splash is 16:9, and the official marks match recorded checksums. |
| `devhound hooks install` | Adds pre-commit (secret scan) and pre-push (funding check) hooks. Never overwrites a hook you wrote unless you pass `--force`; fails open if DevHound isn't installed. |
| `devhound init` | Writes a starter `FUNDING.json`. |
| `devhound mascot` | Prints the husky in your terminal. |

Every command supports `--format text|json|sarif` and `--output FILE`. Exit code `0` = clean, `1` = findings, `2` = usage error.

Marking a false positive: add `devhound:ignore` to that line, or list paths in `.devhoundignore`. Bypass a hook once with `git commit --no-verify`.

## Privacy

Nothing leaves your machine. The CLI imports no networking modules (a test enforces this), has no telemetry, and redacts every detected secret. Full details in [PRIVACY.md](./PRIVACY.md).

## Add-ins

Everything below runs offline except where noted. Details in [`addons/`](./addons/README.md).

| Add-in | Use it for |
|---|---|
| **VS Code extension** | Findings in the Problems panel |
| **Browser extension** | Check text for secrets before pasting it anywhere (network blocked by its CSP) |
| **GitHub Action / pre-commit** | Run the same checks in CI or on every commit |
| **Shell integration** | Tab-completion and `dh`, one word to run every check |
| **Jellyfin applier** | Apply the brand CSS to your media server (talks only to your local server) |

Other editors: output is `file:line:col: level: message`, which most editors already understand. See [`integrations/`](./integrations/).

## Ecosystem roadmap

The wider DevHound plan (IDE plugins, chat bots, browser extension and more) is mapped to what exists today in [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md), with the privacy rules every add-in must follow.

## Docs

[BRAND.md](./BRAND.md) · [PRIVACY.md](./PRIVACY.md) · [SECURITY.md](./SECURITY.md) · [CONTRIBUTING.md](./CONTRIBUTING.md) · [GOVERNANCE.md](./GOVERNANCE.md) · [CHANGELOG.md](./CHANGELOG.md)

## License

Code: [MIT](./LICENSE). The husky mark and wordmark follow the usage terms in [BRAND.md](./BRAND.md).
