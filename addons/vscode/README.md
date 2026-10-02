# DevHound for VS Code / VSCodium

Shows DevHound findings in the Problems panel and status bar. Calls the local `devhound` CLI (falls back to `python3 -m devhound`); no network, no telemetry.

## Install (unpacked, no Marketplace needed)

```bash
cp -r addons/vscode ~/.vscode/extensions/bilbywilby.devhound-vscode-0.1.0      # VS Code
cp -r addons/vscode ~/.vscode-oss/extensions/bilbywilby.devhound-vscode-0.1.0  # VSCodium
```
Restart the editor, open your repo folder, then **Command Palette → DevHound: Scan workspace for secrets**.

Commands: scan, check FUNDING.json, verify brand assets, clear. Setting `devhound.scanOnSave` (off by default) re-scans on save; `devhound.executable` overrides the command.

Findings show the rule, location and a fix hint, never the secret value. Install the CLI first: `pip install .` in the Lil_B repo.

Status: core logic and activation flow are unit-tested with a stubbed VS Code API (`node --test addons/vscode/test/lib.test.js`); not yet run inside a real editor.
