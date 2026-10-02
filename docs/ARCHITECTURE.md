# DevHound Ecosystem: Status and Privacy-First Architecture

This maps the ecosystem spec (10 add-ins plus a core platform) to what exists **today** in this repository, and states the privacy rules each add-in must meet before it ships. Nothing here is marked "done" unless it's implemented and tested.

## Principle: local core, cloud optional

The spec describes a hybrid edge/cloud design. This repo implements the **local edge only**: everything runs on your machine with no network. Any future cloud service (`devhound-core-api`) is optional and must satisfy [PRIVACY.md](../PRIVACY.md). Every add-in talks to the same local contract:

- **Findings format:** SARIF 2.1.0 (`--format sarif`), plus a gcc-style text format editors already parse.
- **Exit codes:** `0` clean, `1` findings, `2` usage error.
- **Rules:** `DH-SEC-*` (secrets), `DH-FUND-*` (funding), `DH-BRAND-*` (brand).

## Status of the 10 add-ins

| # | Add-in | Status | How to use it today | Needed to ship the full version |
|---|---|---|---|---|
| 1 | VS Code / VSCodium | **Config recipe** | `integrations/vscode/tasks.json` → Problems panel via `$gcc`; SARIF Viewer for rich results | Extension (TypeScript/LSP) |
| 2 | JetBrains | **Config recipe** | External Tool or File Watcher running `devhound scan .`; load SARIF | Kotlin plugin |
| 3 | Browser extension | **Not started** | n/a | Manifest V3 extension; must analyze diffs locally unless the user opts in per action |
| 4 | Slack assistant | **Not started** | n/a | Server component; needs hosting and secret management |
| 5 | Discord bot | **Not started** | n/a | Same as Slack |
| 6 | CLI + hooks (`husky-guard`) | **Implemented, tested** | `devhound` (Python, stdlib only) | Optional Go/Rust single binary |
| 7 | Neovim | **Config recipe** | `makeprg` + `errorformat` snippet in `integrations/README.md` | Lua plugin / Telescope picker |
| 8 | Raycast / Alfred | **Not started** | n/a | macOS-only; clipboard features need explicit user action |
| 9 | Docker Desktop extension | **Not started** | n/a | Extension SDK; see privacy note below |
| 10 | Jellyfin | **CSS theme + splash** | `integrations/jellyfin/` (no plugin needed) | C# server plugin only if middleware injection is wanted |

"Config recipe" means documented and low-risk but not verified against every editor version; the CLI behind it is tested.

## Core components

| Spec component | Status |
|---|---|
| `devhound-rules` (FUNDING.json, SPDX, brand rules) | **Implemented** as `devhound/funding.py`, `spdx.py`, `brand.py` |
| `devhound-cdn` (brand assets, CSS variables) | **Static files** in `assets/` and `tokens/`; serve them from any static host |
| `devhound-core-api` (AI audit gateway) | **Not implemented.** Requires a hosted service and a consent/redaction layer |

## Where this implementation differs from the spec, and why

| Spec says | This repo does | Reason |
|---|---|---|
| CLI in Go or Rust | Python, stdlib only | Runs everywhere (Termux, proot) with no build step; a Go/Rust port can reuse the same contract and test cases |
| Validate `BRAND.md` | `BRAND.md` now exists; `devhound brand` checks assets and checksums | The brand guide previously lived in the README |
| Splash as `devhound-splash-1920x1080.svg` | PNG | Jellyfin's uploader is unreliable with SVG |
| Cloud API is the center of the design | Local-first; cloud optional | Privacy: no code leaves the machine by default |
| Telemetry logged to Docker/Jellyfin dashboards | None | No telemetry by design |
| Jellyfin theme injects CSS from middleware | Paste-in CSS, no third-party requests by default | Simpler, auditable, no server code |

## Privacy requirements by add-in (must hold before release)

- **Browser extension:** read diffs from the page locally; sending anything to an API requires a per-action click and shows the payload. No persistent host permissions beyond the sites the user enables.
- **Slack / Discord bots:** store no source code; alert payloads contain rule ID, file path and line, never code or secret values. Document retention.
- **Raycast / Alfred clipboard auditor:** read the clipboard only when the user invokes the command; scan locally; never upload without explicit confirmation.
- **Docker extension:** scanning images locally is fine. Hooking `docker build`/`push` implicitly is invasive; make it an explicit "Scan image" action instead.
- **All add-ins:** tokens in the OS secret store, telemetry off by default, offline mode works.

## Roadmap order (suggested)

1. Publish the CLI (PyPI or GitHub release) and a pre-commit framework hook.
2. VS Code extension wrapping the CLI (SARIF in, diagnostics out).
3. Neovim plugin (thin wrapper over `makeprg`).
4. Only then, optional cloud features behind the consent rules above.
