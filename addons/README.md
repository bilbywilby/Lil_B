# Add-ins

| Add-in | What it does | Install |
|---|---|---|
| [`vscode/`](./vscode/README.md) | Secret/funding/brand findings in the Problems panel | Copy folder to your extensions dir |
| [`browser/`](./browser/README.md) | Scan selected or page text for secrets, fully offline | Load unpacked in Chrome/Edge/Brave |
| [`jellyfin/`](./jellyfin/README.md) | Apply the DevHound CSS to Jellyfin from the command line | `python3 addons/jellyfin/apply_branding.py` |
| [`ci/`](./ci/README.md) | GitHub Action and pre-commit hooks | Add to your workflow / pre-commit config |
| [`shell/`](./shell/README.md) | Tab-completion and the `dh` one-word check (bash, zsh) | `source addons/shell/devhound.sh` |

Every add-in follows [PRIVACY.md](../PRIVACY.md). The Jellyfin applier is the only one that makes a network request, and only to a local server you name.

Tested logic, not yet field-tested: the VS Code, browser, Jellyfin and CI add-ins pass automated tests here but haven't been run inside the real VS Code, a real browser, a live Jellyfin server, or on GitHub.
