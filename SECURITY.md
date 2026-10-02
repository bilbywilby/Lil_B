# Security Policy

## Reporting a vulnerability

Please **don't open a public issue** for security or privacy problems. Use GitHub's private reporting instead:
**Security tab → Report a vulnerability** on this repository.

Include what you found, how to reproduce it, and the version (`devhound --version`). You'll get an acknowledgement as soon as the maintainer can respond; this is a small independent project, so there's no formal SLA.

## Scope

In scope: the `devhound/` package, git hook scripts it writes, and CI workflows in this repo.
Of particular interest: anything that could leak a detected secret, make a network call, or overwrite a user's files unexpectedly.

## If DevHound flags a real secret in your repo

1. **Revoke or rotate it first.** Removing it from the latest commit doesn't remove it from history.
2. Remove it from git history (e.g. `git filter-repo`), then force-push.
3. Load it from an environment variable or secret store instead.
