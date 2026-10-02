# Editor and tool integrations

DevHound prints findings as `path:line:col: level: message [RULE]`, the format compilers use, so most editors show them in the Problems list with **no extension and no network access**.

## VS Code / VSCodium

Copy `vscode/tasks.json` into your project's `.vscode/` folder. Run **Terminal → Run Task → DevHound: scan for secrets**. Findings appear in the Problems panel through the built-in `$gcc` matcher. For richer results, `devhound scan --format sarif -o devhound.sarif` opens in the SARIF Viewer extension.

## Neovim

No plugin needed. Add to your config:

```lua
vim.opt.makeprg = "devhound scan ."
vim.opt.errorformat = "%f:%l:%c: %trror: %m,%f:%l:%c: %tarning: %m,%-G%.%#"
```

Then `:make` fills the quickfix list (`:copen`). Optional mapping: `vim.keymap.set("n", "<leader>dh", "<cmd>make<cr><cmd>copen<cr>")`.

## JetBrains, others

Run `devhound scan --format sarif -o devhound.sarif`; any SARIF-aware tool can load it. Or add a File Watcher / External Tool that runs `devhound scan .`.

## Git

`devhound hooks install` (see the root README).

## Jellyfin

See `jellyfin/README.md`.
