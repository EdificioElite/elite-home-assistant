# Contributing to Edificio Elite

## Branch Protection

The `main` branch is **protected**. Direct pushes are blocked. All changes must go through **Pull Requests**.

### Protection rules active:
- **All CI checks must pass** (ruff, tests, hassfest) before merge
- **No force pushes**
- **No direct deletions**

## Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/my-change
   ```

2. **Make your changes** and ensure CI passes locally:
   ```bash
   ruff check custom_components/
   pytest tests/ -v
   ```

3. **Push the branch** and open a Pull Request:
   ```bash
   git push origin feature/my-change
   gh pr create --title "feat: ..." --body "..."
   ```

4. **Wait for CI to pass** — merge is blocked until all checks pass.

## Release Process

Releases are automated via [release-please](https://github.com/googleapis/release-please-action). No manual version bump is needed.

1. **Merge changes to `main`** using conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, etc.).
2. release-please opens a **release PR** that bumps `custom_components/edificio_elite/manifest.json` and updates `CHANGELOG.md`.
3. **Merge the release PR** — release-please creates the tag `vX.Y.Z` and the GitHub Release automatically.

The version is derived from commit history: `feat!` or `BREAKING CHANGE` triggers a major/minor bump, while `feat:`/`fix:` trigger a minor/patch bump. Config lives in `release-please-config.json` (version tracking in `.release-please-manifest.json`).

## Code Standards

- Run `ruff check custom_components/` before committing
- Tests must pass (`pytest tests/ -v`)
- Home Assistant brand images go in `custom_components/edificio_elite/brand/`
- Do not use `state_class: measurement` with `device_class: energy` or `water`
