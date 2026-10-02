# Changelog

## 0.2.1 (2026-10-01)

### Fixed
- `hooks install` no longer writes into a shared `core.hooksPath` directory unless `--shared` is passed.
- `check` now rejects a non-object `funding_status` and a top-level `seeking_funding`.
- Git tests are hermetic (ignore the developer's global git config), so a personal hook or template can't break them.

### Changed
- `FUNDING.json`: maintainer's allocation (20/30/20/15/15); `project.funding_model` added.

## 0.2.0 / Brand 1.2.0 (2026-10-01)

### Added
- `devhound` offline CLI: `scan`, `check`, `brand`, `hooks`, `init`, `doctor`, `mascot`.
- Secret scanner with redacted output; SARIF 2.1.0 and JSON output formats.
- `FUNDING.json` validator: 5-field breakdown totals exactly 100, strict booleans, sponsor tiers, SPDX (offline subset).
- `husky-guard` git hooks that never overwrite user hooks and fail open.
- Official-mark checksums (`assets/logo/CHECKSUMS.sha256`) and brand verification.
- Jellyfin integration (CSS theme + 16:9 splash), design tokens, VS Code and Neovim recipes.
- PRIVACY.md, SECURITY.md, docs/ARCHITECTURE.md, test suite (30 tests), CI workflow.

### Changed
- Brand guidelines moved from README to BRAND.md; README is now the project overview.
- `FUNDING.json` gains `funding_status`, `use_of_funds_breakdown` (draft allocation), and `privacy` sections.

## 0.1.0 / Brand 1.1.0 (2026-08-05)
- Vector trace of the mascot, icon/favicon set, OG card, render script, issue/PR templates.
