# Privacy

DevHound's local toolkit is built so you never have to trust it with your code.

## Guarantees (and how they're enforced)

| Guarantee | Enforcement |
|---|---|
| **No network access.** The CLI never connects to anything. | `tests/test_devhound.py::PrivacyContractTests` fails the build if any module imports `socket`, `urllib`, `http`, `requests`, `ssl` and similar. |
| **No telemetry, no analytics, no phone-home.** | There is no code path that sends data. `devhound doctor` states this. |
| **Secrets are never printed or stored.** Findings show file, line, rule and fix advice only. | `test_values_never_in_output` checks text, JSON and SARIF output contain no part of a detected secret. Fingerprints are hashes of rule+path+line, never of the secret. |
| **Staged scans read what you're committing**, nothing else. | `scan --staged` reads from the git index. |
| **Hooks never overwrite your own hooks** and fail open if DevHound is missing. | Covered by hook install/uninstall tests. |

## What the tool reads and writes

- Reads: files under the paths you give it (skips `.git`, `node_modules`, binaries, files over 1 MB, and anything in `.devhoundignore`).
- Writes: only what you ask for (`--output`, `init`, `hooks install`, `brand --update-checksums`).

## Rules for any future DevHound add-in

Anything built for the wider ecosystem (see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)) must:

1. **Work offline by default.** Cloud features are opt-in, off at install, and clearly labelled.
2. **Ask before sending code anywhere**, per action, showing exactly what will be sent. No background uploads, no clipboard reads without a user-initiated command.
3. **Redact secrets before any outbound payload**, and never send detected secret values.
4. **Store tokens only in the OS secret store**, never in plain-text config.
5. **Keep telemetry off** (`telemetry_opt_in: false`) unless the user turns it on, with the collected fields documented.
6. **Third-party fetches are optional.** For example, the Jellyfin theme works without the CDN-hosted base theme; enabling it sends your visitors' IPs to that CDN.

## Sponsors and donors

Sponsors appear in the repo only with their written consent (`sponsor_listing_requires_consent` in `FUNDING.json`). Donor names are not published by default.

## Reporting a privacy problem

See [SECURITY.md](./SECURITY.md).
