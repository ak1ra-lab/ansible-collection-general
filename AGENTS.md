# AGENTS.md

This repo **is** the `ak1ra_lab.general` Ansible collection (`galaxy.yml`
namespace/name), not a consumer of it. Content: reusable roles under `roles/`
(`apt_install`, `debian_base`, `docker`, `go_build`,
`pyproject_install`) plus Python modules `github_releases_info` and
`cpu_info` (`plugins/modules/` + shared logic in `plugins/module_utils/`). No `src/` or
pytest suite. See `README.md` for the consume/deploy workflow.

## Tooling - use these, not the defaults

`just <recipe>` is a convenience wrapper for humans; each recipe is a thin
`uv run ...` / `ansible-galaxy ...` (see `justfile`). Agents can call the
underlying command directly - the two are equivalent.

- Env/deps: **uv** (`just sync` = `uv sync --group dev`). Never `pip`/`poetry`.
  Dep group: `lint` (ruff, ty, ansible-core), pulled into `dev` together with
  `pre-commit`.
- Lint+format: **ruff**, scoped to `plugins/` only (`just lint` =
  `uv run ruff check --fix plugins/` then `uv run ruff format plugins/`). Never
  `black`/`isort`/`flake8`.
- Typecheck: **ty** (astral-sh/ty), `plugins/` only (`just typecheck` =
  `uv run ty check plugins/`). Never `mypy`. ty resolves the
  `ansible_collections...` self-imports from `.ansible/collections` (`[tool.ty.environment]`
  in `pyproject.toml`), and the recipe reinstalls the collection first so the
  snapshot is fresh.
- No tests: there is no `tests/` tree and no pytest recipe. Don't invent one.

Python changes to `plugins/` MUST pass ruff lint+format (and ty) before commit.

## Ansible (self-contained layout)

`ansible.cfg` pins `roles_path=./roles` and `collections_path=./.ansible/collections`
and never reaches user-level/parent paths.

Because the modules (`github_releases_info`, `cpu_info`) import their own
`module_utils` via the absolute path
`ansible_collections.ak1ra_lab.general.plugins.module_utils...`,
the collection must be **installed into itself** for the modules (ty and
ansible-lint) to resolve. Install the collection before typechecking, linting,
or running playbooks:

```shell
just ansible-collection-install   # = ansible-galaxy collection install --force -p .ansible/collections .
```

- `requirements.yaml` deps (`ansible.posix`, `community.general`) are usually
  already present at user level, so installing the collection itself is enough.
- `ansible-lint` runs with `profile: production` (`.ansible-lint`); in non-`offline`
  mode it auto-installs `requirements.yaml` into a cache dir computed by
  ansible-compat from the project dir, ignoring `ansible.cfg`'s `collections_path`.
- `.ansible-lint` intentionally has no `kinds:` mapping: remapping role
  `defaults/` (or `vars/`) files out of the default "vars" kind silently
  disables `var-naming[no-role-prefix]` for the role. Role variables use the
  `<role>_*` prefix (see `roles/apt_install/README.md`).
- The `roles/pyproject_install/molecule/` scenario is dormant - don't rely on it.

Ansible changes MUST pass `ansible-lint` before commit.

