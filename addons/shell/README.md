# Shell integration (bash and zsh)

```bash
echo 'source ~/Lil_B/addons/shell/devhound.sh' >> ~/.zshrc    # or ~/.bashrc
```

- **Tab-completion** for `devhound` commands, options and values (`--format text|json|sarif`). Generated from the real CLI, so it can't drift.
- **`dh`**: runs the secret scan, the funding check and (in repos with brand assets) the brand check, one line each. Exit code is non-zero if any failed. Works even if `devhound` isn't on PATH (falls back to `python3 -m devhound`).

zsh uses its built-in bash-completion compatibility layer; the completion logic itself is tested in bash. Not yet tried in a real zsh.
