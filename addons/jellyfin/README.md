# Jellyfin branding applier

Applies the DevHound CSS to your Jellyfin server without copy-pasting.

```bash
export JELLYFIN_API_KEY=...            # Dashboard > Advanced > API Keys (admin key)
python3 addons/jellyfin/apply_branding.py            # plan: shows what would change, changes nothing
python3 addons/jellyfin/apply_branding.py apply      # backs up current branding, then applies
python3 addons/jellyfin/apply_branding.py restore jellyfin-branding-backup-YYYYMMDD-HHMMSS.json
```

- Default server: `http://127.0.0.1:8096`; change with `--url http://192.168.0.189:8096`. Non-local addresses need `--allow-remote`.
- Only `CustomCss` is changed. Your login disclaimer and other branding stay as they are.
- `--monochromic` applies the variant that loads a base theme from a CDN (see `integrations/jellyfin/README.md` for the privacy trade-off).
- The key comes from the environment or a hidden prompt, never from the command line.
- The splash image is not handled here; upload it once in Dashboard > Branding.

Tested against a mock server that mirrors Jellyfin's documented branding endpoints. Not yet run against a live server, so use `plan` first.
