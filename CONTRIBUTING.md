# Contributing to Elite Climate

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

1. **Bump the version** in a PR (example commit message: `chore: bump version to 0.3.0`):
   - Edit `custom_components/elite_climate/manifest.json` and update the `"version"` field
   - Create a PR, wait for CI, and merge it

2. **Run the release workflow**:
   ```bash
   gh workflow run Release
   ```
   This reads the current version from `manifest.json`, creates a tag, and publishes a GitHub Release.

## Code Standards

- Run `ruff check custom_components/` before committing
- Tests must pass (`pytest tests/ -v`)
- Home Assistant brand images go in `custom_components/elite_climate/brand/`
- Do not use `state_class: measurement` with `device_class: energy` or `water`
