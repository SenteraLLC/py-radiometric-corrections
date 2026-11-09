# Repository guidance

This package corrects multispectral drone imagery. `imgcorrect/` contains the
library, `scripts/` contains CLI/GUI entry points, and `tests/` contains real
sensor imagery and ArUco marker fixtures.

## Development and validation

- Keep dependency ranges in `pyproject.toml` and `environment.yml` consistent;
  regenerate `poetry.lock` with `poetry lock`.
- Select an interpreter with `poetry env use`, then run `poetry install`.
- ExifTool must be on PATH for non-Windows image-correction tests.
- Run `poetry run pytest` and `prek run --all-files`.
- CI tests Python 3.10 and 3.14. Test both supported endpoints when changing
  dependencies; pandas 3 is available only on Python 3.11 and newer.
- Marker tests must exercise the production panel-detection path. Preserve
  panel geometry, supported marker IDs, and the low-contrast NIR fallback.

## Guardrails

- Do not modify or delete input image fixtures.
- Correction tests write to `tests/output/` and remove that directory at teardown;
  do not keep user data there.
- Do not tag a release based only on dependency resolution: run marker detection
  and the full image-correction fixture suite first.
