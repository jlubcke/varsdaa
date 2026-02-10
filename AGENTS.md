# Agent Guide (varsdaa)

Small Django app (Django + iommi + django-allauth) using:
- `uv` for env/deps (`uv.lock` is committed)
- `ruff` for linting/formatting
- `pytest` + `pytest-django` for tests

## Project Layout

- `varsdaa/`: app code (models, views, iommi wrappers, map rendering)
- `django_site/django_site/`: Django site package (`settings.py`, etc.)
- `varsdaa/test/settings.py`: test settings used by pytest
- `pyproject.toml`: deps + tool config (pytest, ruff)

## Setup

```bash
uv sync --dev
uv run python -V
```

Requires Python `>=3.14` (see `pyproject.toml`).

## Commands

### Run (dev)

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Useful Django utilities:

```bash
uv run python django_site/manage.py check
uv run python django_site/manage.py makemigrations
uv run python django_site/manage.py shell
```

### Lint / Format

Ruff is the source of truth.

```bash
uv run ruff format .
uv run ruff format . --check
uv run ruff check .
uv run ruff check . --fix
```

Repo ruff defaults: line length 120; `E501` ignored; import sorting enabled; formatter preserves existing quote style.

### Tests

Pytest uses `DJANGO_SETTINGS_MODULE = "varsdaa.test.settings"` (configured in `pyproject.toml`).

```bash
uv run pytest
uv run pytest -q
uv run pytest -x
uv run pytest -vv
```

Run a single test file:

```bash
uv run pytest varsdaa/tests.py
```

Run a single test (node id; preferred):

```bash
uv run pytest varsdaa/tests.py::test_register
```

Run a subset by keyword:

```bash
uv run pytest -k register
```

## Cursor / Copilot Rules

- Cursor rules: none found in `.cursor/rules/` or `.cursorrules`
- Copilot rules: none found in `.github/copilot-instructions.md`
If these are added later, treat them as higher priority than this file.

## Code Style Guidelines

### Imports

- Group imports: standard library, third-party, local (`varsdaa.*`) with a blank line between groups
- Keep imports sorted (ruff enforces this); avoid unused imports
- Prefer explicit imports over wildcard imports

### Formatting

- Run `uv run ruff format .` before committing
- Stay close to 120 columns even though `E501` is ignored
- Quote style is `preserve`: match existing file conventions when editing

### Types

- Add type hints when they clarify intent (public helpers, non-trivial return types, adapters/managers)
- Prefer modern typing: `X | None`, `list[str]`, `dict[str, Any]`
- If Django/base-class overrides fight the type checker, use narrow `# type: ignore[...]` (see `varsdaa/models.py`)

### Naming

- Classes: `PascalCase` (`UserTable`, `RoomForm`, `SocialAccountAdapter`)
- Functions/vars: `snake_case` (`register_display_url`, `desk_pk_for_user`)
- Constants: `UPPER_SNAKE_CASE`
- Django fields: `snake_case`; be explicit about `null=True` vs `blank=True`

### Django Conventions

- Prefer `get_object_or_404()` for request-driven lookups
- Prefer `timezone.now()` for timestamps
- Keep `get_absolute_url()` stable; use `reverse()` when a named URL exists
- Use `select_related()`/`prefetch_related()` when rendering lists to avoid N+1

### Error Handling

- Catch specific ORM exceptions (`DoesNotExist`, `MultipleObjectsReturned`) when needed
- Avoid blanket `except Exception:`; if you must, re-raise or log with clear context
- For API-ish views, prefer `JsonResponse` and explicit status codes

### iommi Conventions (repo-specific)

- Prefer the wrappers in `varsdaa/iommi.py`: `Page`, `Table`, `Form`, `Field`, `Column`
- Use double-underscore refinables (`parts__x`, `columns__y__filter__include`) consistently
- `Map` in `varsdaa/map.py` expects `*_all` and `*_marked` refinables; keep naming consistent

### Tests

- Use pytest fixtures + plain `assert`
- Mark DB tests with `pytest.mark.django_db` (module-level `pytestmark` is fine)
- Prefer node ids (`file.py::test_name`) for single-test runs

### Security / Secrets

- Do not commit real secrets (OAuth client secrets, production `SECRET_KEY`, etc.)
- Dev settings live in `django_site/` + `manage.py`; test settings live in `varsdaa/test/`

## Change Checklist

- `uv run ruff format .` and `uv run ruff check .`
- `uv run pytest` (or at least the relevant node ids)
- If you change models: create/review migrations; keep them minimal
