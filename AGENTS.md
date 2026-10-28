# AGENTS.md

This repo **is** the `ak1ra_lab.general` Ansible collection (`galaxy.yml`
namespace/name), not a consumer of it. Content: reusable roles under `roles/`
(`acme_dns`, `acme_dns_register`, `apt_install`, `cert_manager`, `certbot`,
`debian_base`, `docker`, `go_build`, `pyproject_install`) plus Python modules
`github_releases_info` and `cpu_info` (`plugins/modules/` + shared logic in
`plugins/module_utils/`). No `src/` or pytest suite; Ansible behavior is covered
by Molecule scenarios (see Testing).
See `README.md` for the consume/deploy workflow and `CONTRIBUTING.md` for the
human contributor workflow.

## Tooling - use these, not the defaults

`just <recipe>` is a convenience wrapper for humans; each recipe is a thin
`uv run ...` / `ansible-galaxy ...` (see `justfile`). Agents can call the
underlying command directly - the two are equivalent.

- Env/deps: **uv** (`just sync` = `uv sync --group dev`). Never `pip`/`poetry`.
  Dep groups: `lint` (ruff, ty, ansible-core, antsibull-docs) and `docs`
  (MkDocs Material, mkdocs-ansible-collection, markup parser, link checker),
  pulled into `dev` together with `pre-commit`.
- Lint+format: **ruff**, scoped to `plugins/` only (`just lint` =
  `uv run ruff check --fix plugins/` then `uv run ruff format plugins/`). Never
  `black`/`isort`/`flake8`.
- Typecheck: **ty** (astral-sh/ty), `plugins/` only (`just typecheck` =
  `uv run ty check plugins/`). Never `mypy`. ty resolves the
  `ansible_collections...` self-imports from `.ansible/collections` (`[tool.ty.environment]`
  in `pyproject.toml`), and the recipe reinstalls the collection first so the
  snapshot is fresh.
- Molecule: `just molecule-test` / `molecule-test-one <scenario>` /
  `molecule-list`; the scenarios live under `extensions/molecule/` (see
  Testing below).
- Docs: `just docs-build` (role coverage check plus `mkdocs build --strict`),
  `just docs-serve`, `just docs-check`, and `just docs-lint` (antsibull-docs
  collection lint). `mkdocs.yaml` is excluded from ansible-lint.

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

- `requirements.yaml` deps (`ansible.posix`, `community.general`,
  `containers.podman`, `community.docker`, `kubernetes.core`) provide the role
  runtime and the Molecule container lifecycle;
  `just ansible-requirements-install` installs them into the project-local
  path.
- `ansible-lint` runs with `profile: production` (`.ansible-lint`); in non-`offline`
  mode it auto-installs `requirements.yaml` into a cache dir computed by
  ansible-compat from the project dir, ignoring `ansible.cfg`'s `collections_path`.
- `.ansible-lint` intentionally has no `kinds:` mapping: remapping role
  `defaults/` (or `vars/`) files out of the default "vars" kind silently
  disables `var-naming[no-role-prefix]` for the role. Role variables use the
  `<role>_*` prefix (see `roles/apt_install/README.md`).

## Documentation (single source)

The MkDocs site is a presentation layer, not a second source of truth.

- Role contracts live in `roles/<role>/README.md`; `docs/roles/<role>.md` is a
  one-line `--8<--` snippet. Never copy role content into the docs page.
- Module reference is generated from `plugins/modules/*.py` `DOCUMENTATION`,
  `EXAMPLES`, and `RETURN`. `hooks/ansible_markup.py` renders Ansible markup in
  the generated pages.
- `docs/contributing.md` and `docs/changelog.md` include `CONTRIBUTING.md` and
  `CHANGELOG.md`; edit the source files.
- Hand-written pages are `docs/index.md`, `docs/installation.md`,
  `docs/architecture.md`, `docs/playbooks.md`, and `docs/modules.md`.
- Adding a role requires the role README, the docs stub, the `Roles` nav entry,
  and the `docs/roles/index.md` table entry. `just docs-check` enforces this.
- Do not add hand-maintained translated siblings; keep the site English-only
  unless a translation workflow is added.
- Included Markdown must use absolute URLs for repository file links; relative
  file links resolve against the including docs page.

Docs changes MUST pass `just docs-check` and `just docs-build`; module
documentation changes MUST also pass `just docs-lint`.

## Testing (Molecule)

Ansible behavior is covered by ansible-native Molecule scenarios under
`extensions/molecule/` (collection-testing layout). See `CONTRIBUTING.md` for
the scenario matrix, container runtime, and prerequisites. There is no
`tests/` tree and no pytest recipe - do not invent one.

Agent-specific constraints:

- The `default` scenario owns the shared container lifecycle; component
  scenarios reuse the containers. `config.yml` sets `shared_state: true` and
  the component sequence (cleanup, prepare, converge, idempotence, verify,
  cleanup, verify `absent-verify.yml`).
- The recipes install the collection under test before every run. When
  invoking `molecule` directly, run `just ansible-collection-install` after
  editing a role, or the scenario tests the previously installed copy.
- Molecule caches scenario state, so a changed `molecule.yml` needs
  `molecule reset` (or `destroy`).

Ansible changes MUST pass `ansible-lint` and the Molecule suite before commit.

