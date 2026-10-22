# AGENTS.md

This repo **is** the `ak1ra_lab.general` Ansible collection (`galaxy.yml`
namespace/name), not a consumer of it. Content: reusable roles under `roles/`
(`acme_dns`, `acme_dns_register`, `apt_install`, `cert_manager`, `certbot`,
`debian_base`, `docker`, `go_build`, `pyproject_install`) plus Python modules
`github_releases_info` and `cpu_info` (`plugins/modules/` + shared logic in
`plugins/module_utils/`). No `src/` or pytest suite; Ansible behavior is covered
by Molecule scenarios (see Testing).
See `README.md` for the consume/deploy workflow.

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
- Molecule: `just molecule-test` / `molecule-test-one <scenario>` /
  `molecule-list`; the scenarios live under `extensions/molecule/` (see
  Testing below).

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

## Testing (Molecule)

Ansible behavior is covered by ansible-native Molecule scenarios under
`extensions/molecule/` (collection-testing layout; there is no `tests/` tree
and no pytest recipe - don't invent one).

- `config.yml` - shared config: the project inventory, the project-local
  collections path, `shared_state: true`, and the component test sequence
  (cleanup, prepare, converge, idempotence, verify, cleanup, verify
  `absent-verify.yml`).
- `default/` - the only lifecycle manager (`create` / `destroy`); it creates
  the shared Debian 12/13 systemd containers from
  `ghcr.io/ak1ra-lab/docker-systemd`.
- `<role>/...` - one scenario directory per role, nested where a role needs
  several scenarios (`apt_install/basic`, `apt_install/variants`,
  `pyproject_install/local`, `pyproject_install/pypi`). Nested scenario
  prepare playbooks import the shared preparation with
  `../../shared/prepare.yml`.
- Containers run on Podman by default; set `MOLECULE_CONTAINER_RUNTIME=docker`
  for a rootful Docker daemon.

Prerequisites: `just ansible-collection-install` and
`just ansible-requirements-install` (Molecule's dependency action is disabled,
because the shared lifecycle scenario runs before ansible-compat's prerun).
`go` and `uv` must be on the controller `PATH` for the `go_build` and
`pyproject_install` scenarios.

```shell
just molecule-test                        # every scenario
just molecule-test-one apt_install/basic  # one scenario
just molecule-list
```

The molecule recipes reinstall the collection under test first; when invoking
`molecule` directly, run `just ansible-collection-install` after editing a
role, or the scenario tests the previously installed copy. Molecule caches
scenario state, so a changed `molecule.yml` needs `molecule reset` (or
`destroy`).

Ansible changes MUST pass `ansible-lint` and the Molecule suite before commit.

