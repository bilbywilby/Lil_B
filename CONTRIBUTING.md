# Contributing to DevHound

Thanks for your interest in contributing. This document covers how to propose changes to this repository, including brand assets.

## Before you start

- Search existing issues before opening a new one.
- For anything beyond a small fix, open an issue first to discuss the change.

## Making changes

1. Fork the repository and create a branch from `main`.
2. Make your change.
3. If you're changing anything under `assets/logo/`, edit the master vector (`assets/logo/husky-primary.svg`) and regenerate the rest with:
   ```bash
   python3 scripts/render.py
   ```
   Don't hand-edit the generated PNG files directly — they'll be overwritten the next time someone runs the script.
4. Open a pull request describing what changed and why.

## Brand asset changes

Changes to the mascot, wordmark, or color palette should follow [README.md](./README.md) (which doubles as the brand guideline document) and be flagged clearly in the PR description, since these affect every downstream consumer of the assets.

## Code of conduct

Be respectful and constructive. Disagreements about design or implementation are fine; personal attacks are not.
