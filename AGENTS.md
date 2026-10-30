# AGENTS.md

This repo **is** the `ak1ra_lab.general` Ansible collection (`galaxy.yml`
namespace/name), not a consumer of it. Content: reusable roles under `roles/`
(`apt_install`, `debian_base`, `docker`, `go_build`, `pyproject_install`),
Python modules `github_releases_info` and `cpu_info` (`plugins/modules/` plus
shared logic in `plugins/module_utils/`), and the `random_*` lookup plugins
(`plugins/lookup/`, unit-tested under `tests/unit/`). Ansible behavior is
covered by Molecule scenarios (see Testing).
See `README.md` for the consume/deploy workflow and `CONTRIBUTING.md` for the
human contributor workflow.

## Tooling - use these, not the defaults

`just <recipe>` is a convenience wrapper for humans; each recipe is a thin
`uv run ...` / `ansible-galaxy ...` (see `justfile`). Agents can call the
underlying command directly - the two are equivalent.

- Env/deps: **uv** (`just sync` = `uv sync --group dev`). Never `pip`/`poetry`.
  Dep groups: `lint` (ruff, mypy, ansible-lint, ansible-core, antsibull-docs,
  galaxy-importer), `test` (tox, tox-ansible), and `docs` (MkDocs Material,
  mkdocs-ansible-collection, markup parser, link checker), pulled into `dev`
  together with `pre-commit`.
- Lint+format: **ruff**, scoped to `plugins/` and `tests/` (`just lint` =
  `uv run ruff check --fix plugins/ tests/` then
  `uv run ruff format plugins/ tests/`). Never `black`/`isort`/`flake8`.
- Typecheck: **mypy** with the pragmatic config in `pyproject.toml`
  (`just typecheck` = `uv run mypy plugins/ tests/`). The recipe reinstalls the
  collection into `.ansible/collections` first so the
  `ansible_collections.ak1ra_lab.general...` self-imports resolve
  (`mypy_path` in `pyproject.toml`). `ansible-test sanity` remains the
  authoritative gate.
- Test harness: **tox-ansible**. `just tox-list` lists the matrix;
  `just tox <env>` runs one environment, for example
  `just tox sanity-py3.13-2.21`. `just unit-test` runs
  `unit-py3.13-2.21` through `ansible-test units`. Do not add a `ty`/pytest
  path as a second test harness.
- Molecule: `just molecule-test` / `molecule-test-one <scenario>` /
  `molecule-list`; the scenarios live under `extensions/molecule/` (see
  Testing below).
- Docs: `just docs-build` (role coverage check plus `mkdocs build --strict`),
  `just docs-serve`, `just docs-check`, and `just docs-lint` (antsibull-docs
  collection lint). `mkdocs.yaml` is excluded from ansible-lint.

Python changes to `plugins/` and `tests/` MUST pass ruff lint+format and mypy
before commit; the unit tests must pass through tox-ansible.

## Ansible (self-contained layout)

`ansible.cfg` pins `roles_path=./roles` and `collections_path=./.ansible/collections`
and never reaches user-level/parent paths.

Because the modules (`github_releases_info`, `cpu_info`) import their own
`module_utils` via the absolute path
`ansible_collections.ak1ra_lab.general.plugins.module_utils...`,
the collection must be **installed into itself** for the modules (mypy and
ansible-lint) to resolve. Install the collection before typechecking, linting,
or running playbooks:

```shell
just ansible-collection-install   # = ansible-galaxy collection install --force -p .ansible/collections .
```

- `requirements.yml` plus `meta/execution-environment.yml` declare only the
  runtime collection dependencies for ansible-builder; the collection has no
  controller-side Python requirements. Test-only collections live in
  `tests/molecule/requirements.yml` and are installed by Molecule's dependency
  action or tox-ansible/ade.
- `ansible-lint` runs with `profile: production` (`.ansible-lint`); in non-`offline`
  mode it auto-installs the `galaxy.yml` dependencies into a cache dir computed
  by ansible-compat from the project dir, ignoring `ansible.cfg`'s
  `collections_path`.
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
  `docs/architecture.md`, `docs/playbooks.md`, `docs/modules.md`, and
  `docs/lookups.md`.
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
`extensions/molecule/` (collection-testing layout). Python plugins and
module_utils are covered by unit tests under `tests/unit/`, run through
`ansible-test units` inside the tox-ansible `unit-*` environments. See
`CONTRIBUTING.md` for the scenario matrix, container runtime, and
prerequisites.

The tox-ansible matrix is configured by `[tool.tox]`/`[tool.tox-ansible]` in
`pyproject.toml` and follows the upstream ansible-core support matrix
(2.19/2.20/2.21 plus weekly devel/milestone). Test-only collections are
declared in `tests/molecule/requirements.yml`; tox-ansible installs them with
`ade`, so do not pre-install into `.ansible/collections` for test runs.

Agent-specific constraints:

- Scenarios are flat under `extensions/molecule/<name>/` and each one owns its
  containers. `config.yml` maps the shared `create.yml`/`destroy.yml` playbooks
  and the default sequence (dependency, destroy, create, prepare, converge,
  idempotence, verify, cleanup, verify `absent-verify.yml`, destroy). Container
  names include the scenario name and a checkout hash.
- Do not pre-install the collection or test collections into
  `.ansible/collections` for Molecule. The dependency action installs
  `tests/molecule/requirements.yml` and ansible-compat's prerun installs the
  collection under test and its `galaxy.yml` dependencies.
- `just ansible-collection-install` remains the project-local install for lint,
  mypy, and docs only.
- Molecule caches scenario state, so a changed `molecule.yml` needs
  `molecule reset` (or `destroy`).

Ansible changes MUST pass `ansible-lint` and the Molecule suite before commit.

