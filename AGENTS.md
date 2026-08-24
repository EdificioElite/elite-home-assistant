# AGENTS.md — Edificio Elite (Home Assistant Custom Integration)

## What this is
A Home Assistant custom integration for Edificio Elite residents. Monitors aerothermal climate and hot water consumption via JWT-authenticated cloud API.

## Project layout

```
custom_components/edificio_elite/   # Integration code (entry: __init__.py)
tests/                             # pytest tests
assets/                            # Logo for README
.brand/                            # icon.png + logo.png (HA 2026.3+ requirement)
```

## Developer commands

```bash
# Lint (ruff — must pass before commit)
ruff check custom_components/

# Run tests (requires homeassistant + pytest-homeassistant-custom-component)
pip install homeassistant pytest pytest-homeassistant-custom-component pytest-cov
pytest tests/ -v
```

CI runs `ruff check custom_components/`, `pytest tests/`, and `hassfest` on every push.

## Branch protection (DO NOT push to main)

The `main` branch is **protected**. Direct pushes are rejected. All changes must go through **feature branches + Pull Requests** (no approving reviews required, but CI must pass). See `CONTRIBUTING.md` for the full workflow.

## Release workflow

Releases are automated via [release-please](https://github.com/googleapis/release-please-action). No manual version bump is needed.

1. Merge changes to `main` using conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, etc.).
2. release-please opens a **release PR** that bumps `manifest.json` and updates `CHANGELOG.md`.
3. Merge the release PR — release-please creates the tag `vX.Y.Z` and the GitHub Release automatically.

The version is derived from commit history; `feat!` or `BREAKING CHANGE` triggers a major/minor bump, `feat:`/`fix:` a minor/patch bump. Config lives in `release-please-config.json` (version tracking in `.release-please-manifest.json`).

See `CONTRIBUTING.md` for the full workflow.

## Home Assistant brand images (critical for icons)

Home Assistant 2026.3+ requires brand images inside the integration folder:

```
custom_components/edificio_elite/brand/
  icon.png    # 256x256, RGB or RGBA PNG
  logo.png    # optional, rectangular logo
```

Putting `icon.png` in the integration root or repo root is **not sufficient** for HA 2026.3+. The `brand/` subfolder is mandatory for custom integrations to display icons in the integration dashboard.

## Sensor `state_class` rules

Home Assistant is strict about `state_class` + `device_class` combinations:

| device_class | Valid state_class |
|---|---|
| `energy`, `water` | `None`, `total`, `total_increasing` |
| `temperature`, `power` | `measurement` is OK |

Using `measurement` with `energy` or `water` causes log warnings and can break entity registration.

## Binary sensor quirks

The `power_w` field from the API arrives as a **string**. Always cast before comparison:

```python
try:
    return float(power_w) > 0
except (ValueError, TypeError):
    return None
```

## HACS metadata

- `hacs.json` must be in repo root
- `render_readme: true` tells HACS to render the README in the UI
- The `icon.png` in the repo root is for HACS store listing (separate from HA's `brand/` requirement)

## Testing notes

- Tests use `pytest-homeassistant-custom-component` fixtures
- `AsyncMock` import must actually be used — ruff F401 will fail CI if unused
- `datetime.timezone` import must be used — same lint rule applies

## Manifest

`custom_components/edificio_elite/manifest.json` is the single source of truth for:
- Domain, name, version
- Dependencies, config_flow flag
- IoT class, documentation URL

The version field is bumped automatically by release-please (see `release-please-config.json`).
