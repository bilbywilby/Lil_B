# Contributing to DevHound

Thanks for helping. This project is privacy-first: changes that add network access or telemetry to the local toolkit won't be merged (a test enforces the no-network rule).

## Setup

```bash
git clone git@github.com:bilbywilby/Lil_B.git && cd Lil_B
python3 -m unittest discover -s tests   # 60+ tests; Node tests run too if node is installed
python3 -m devhound scan .              # must be clean
python3 -m devhound check && python3 -m devhound brand
```

Optional: `devhound hooks install` to run the secret scan on your own commits.

## Making changes

1. Fork and branch from `main`.
2. Add or update tests with your change.
3. Run the commands above; CI runs the same ones.
4. Open a PR describing what and why.

## Logo and brand changes

1. Edit the master vector `assets/logo/husky-primary.svg`.
2. Regenerate derived files: `python3 scripts/render.py` (needs Pillow and numpy; derived PNGs shouldn't be hand-edited).
3. Update the splash if the artwork changed.
4. `devhound brand --update-checksums`, and add a line to `CHANGELOG.md`.

Follow [BRAND.md](./BRAND.md): the D collar tag must stay intact.

## Code style

Python 3.9+, standard library only in `devhound/`. Findings must never contain secret values.

## Code of conduct

Be respectful and constructive.

## Add-ins

- Browser rules and shell completion are **generated**. After changing `devhound/secrets.py` or the CLI, run `python3 scripts/gen_browser_rules.py` and `python3 scripts/gen_completions.py`; tests fail if they're stale.
- Add-ins must follow [PRIVACY.md](./PRIVACY.md): no network by default, no telemetry, never display secret values.
