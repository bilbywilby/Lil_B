# CI integrations

## GitHub Action

```yaml
# .github/workflows/devhound.yml
name: DevHound
on: [push, pull_request]
permissions:
  contents: read
jobs:
  devhound:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: bilbywilby/Lil_B@main      # pin a tag or commit SHA when you can
        with:
          scan: 'true'
          funding: 'true'
          brand: 'false'
          sarif: devhound.sarif          # optional
```

Inputs: `scan`, `funding`, `brand`, `strict`, `paths`, `sarif`. All checks run even if one fails; the job fails if any did. The action installs from its own checkout (no package registry, no network calls while scanning). Inputs reach the shell through environment variables, not string interpolation, so they can't inject commands.

## pre-commit framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/bilbywilby/Lil_B
    rev: main
    hooks:
      - id: devhound-scan
      - id: devhound-funding
```

`pre-commit install` then blocks commits that contain secrets. (If you don't use the pre-commit framework, `devhound hooks install` does the same without it.)

Neither integration has run on GitHub yet; the logic is tested locally (see `tests/test_addons.py`).
