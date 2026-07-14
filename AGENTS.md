# AGENTS.md

This repo **is** the `ak1ra_lab.general` Ansible collection (`galaxy.yml`
namespace/name), not a consumer of it. Content: reusable roles under `roles/`
(`apt_install`, `debian_base`, `docker`, `go_build`, `go_install`,
`pyproject_install`) plus one Python module `github_releases`
(`plugins/modules/` + shared logic in `plugins/module_utils/`). No `src/` or
pytest suite. See `README.md` for the consume/deploy workflow.

## Tooling - use these, not the defaults

`just <recipe>` is a convenience wrapper for humans; each recipe is a thin
`uv run ...` / `ansible-galaxy ...` (see `justfile`). Agents can call the
underlying command directly - the two are equivalent.

- Env/deps: **uv** (`just sync` = `uv sync --group dev`). Never `pip`/`poetry`.
  Dep groups: `lint` (ruff, ty), `docs` (mkdocs-material, i18n), both pulled into `dev`.
- Lint+format: **ruff**, scoped to `plugins/` only (`just lint` =
  `uv run ruff check --fix plugins/` then `uv run ruff format plugins/`). Never
  `black`/`isort`/`flake8`.
- Typecheck: **ty** (astral-sh/ty), `plugins/` only (`just typecheck` =
  `uv run ty check plugins/`). Never `mypy`.
- Docs: `just docs-build` / `docs-serve` = `uv run --group docs mkdocs ...`.
- No tests: there is no `tests/` tree and no pytest recipe. Don't invent one.

Python changes to `plugins/` MUST pass ruff lint+format (and ty) before commit.

## Ansible (self-contained layout)

`ansible.cfg` pins `roles_path=./roles` and `collections_path=./.ansible/collections`
and never reaches user-level/parent paths.

Because the `github_releases` module imports its own `module_utils` via the
absolute path `ansible_collections.ak1ra_lab.general.plugins.module_utils...`,
the collection must be **installed into itself** for the module (and ansible-lint)
to resolve. Install the collection before linting or running playbooks:

```shell
just ansible-collection-install   # = ansible-galaxy collection install --force -p .ansible/collections .
```

- `requirements.yaml` deps (`ansible.posix`, `community.general`) are usually
  already present at user level, so installing the collection itself is enough.
- `ansible-lint` runs with `profile: production` (`.ansible-lint`); in non-`offline`
  mode it auto-installs `requirements.yaml` into a cache dir computed by
  ansible-compat from the project dir, ignoring `ansible.cfg`'s `collections_path`.
- `just ansible-collection-build` packages a tarball into `.ansible/dist/`.
- The `roles/pyproject_install/molecule/` scenario is dormant - don't rely on it.

Ansible changes MUST pass `ansible-lint` before commit.

## Docs (bilingual)

`docs/` is served by mkdocs-material with the i18n plugin
(`docs_structure: suffix`): every page has an English `*.md` and a
Simplified-Chinese `*.zh.md` sibling (`index`, `installation`, `roles`,
`modules`). When adding or changing a page, update BOTH languages and add its
title to the `nav` plus the `zh` `nav_translations` map in `mkdocs.yml`.
