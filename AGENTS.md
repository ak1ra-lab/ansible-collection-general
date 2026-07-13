# AGENTS.md

## What This Project Does

`ak1ra_lab.general` is a shared Ansible collection of reusable roles and custom
modules for Debian/Ubuntu bootstrap, package management, local build helpers, and
task-specific automation. See `README.md` for consumer setup and role/module details.

## Environment & Tooling - CRITICAL

- **Python package manager:** `uv` (MUST NOT use pip or poetry).
- **Python version:** >= 3.11

Install dev tooling and sync the venv:

    uv sync --group dev

Lint all the things (run before committing):

    uv run ruff check --fix plugins/
    uv run ruff format plugins/
    ansible-lint       # production profile, lints playbooks/, roles/, etc.
    yamlfmt            # external Go tool; format YAML files per .yamlfmt.yaml
    pre-commit run --all-files

Build the collection:

    mkdir -p ./.ansible/dist
    ansible-galaxy collection build --force --output-path .ansible/dist/ .

The collection has NO Python runtime dependencies. `pyproject.toml` exists
solely for dev tooling and is not a Python package (`package = false`).

## Path Conventions

- `ansible.cfg` sets `collections_path=./.ansible/collections` and
  `roles_path=./roles`. No user-level (`~/.ansible/collections`, etc.) paths are
  included. All dependencies come from `requirements.yaml` (tracked) or
  `requirements.dev.yaml` (git-ignored).
- Install collection dependencies and the project's own collection before
  running playbooks. Playbooks reference roles by FQCN
  (`ak1ra_lab.general.<role>`), so the local collection must be installed:

      cp --update=none requirements.yaml requirements.dev.yaml
      ansible-galaxy collection install -r requirements.dev.yaml -p ./.ansible/collections
      ansible-galaxy collection install --force --collections-path .ansible/collections .

- `requirements.dev.yaml` is listed in `.gitignore` and may reference local
  Git repos or file paths for in-development dependency collections.
- `ansible-galaxy collection build --force --output-path .ansible/dist/ .` can
  verify `galaxy.yml`'s `manifest.directives` produce a clean tarball (no
  unintended files).

## Conventions

- Role variable names MUST be prefixed with the role name (e.g., `debian_base_*`,
  `go_build_*`, `pyproject_install_*`). ansible-lint enforces this.
- `import_role` calls MUST use the fully qualified collection name
  (`ak1ra_lab.general.<role_name>`).
- APT repositories MUST use DEB822 `.sources` format via
  `ansible.builtin.deb822_repository`. Legacy `.list` files MUST be removed.
- Roles that build/install on the controller (`go_build`, `go_install`,
  `pyproject_install/local`) MUST set `delegate_to: localhost` and
  `run_once: true` on every task.
- Custom modules follow the standard Ansible split: `plugins/modules/` for entry
  points, `plugins/module_utils/` for shared library code.
- Playbook names use kebab-case: `<role>-<variant>.yaml`.

## Testing Guidelines

There are NO automated tests. Roles are vetted by running playbooks manually:

    ansible-playbook playbooks/debian-base-defaults.yaml -e 'playbook_hosts=<target>'
    ansible-playbook playbooks/docker-vps.yaml -e 'playbook_hosts=<target>'

If tests are added, use Molecule for role integration testing. Update
`galaxy.yml` `manifest.directives` if you add `molecule/` directories (they are
currently excluded from the build).

## Common Operations

    uv sync --group dev                                                  # install dev tooling
    uv run ruff check --fix plugins/ && uv run ruff format plugins/      # lint Python
    ansible-lint                                                         # lint playbooks & roles
    ansible-galaxy collection install --force --collections-path .ansible/collections .  # install for testing
    ansible-galaxy collection build --force --output-path .ansible/dist .        # build release tarball
    pre-commit run --all-files                                           # run all git hooks
