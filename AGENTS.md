# AGENTS.md

## What This Project Does

`ak1ra_lab.general` is a shared Ansible collection of reusable roles and custom
modules for Debian/Ubuntu bootstrap, package management, local build helpers, and
task-specific automation. See `README.md` for consumer setup and role/module details.

## Environment & Tooling - CRITICAL

- **Python package manager:** `uv` (MUST NOT use pip or poetry).
- **Task runner:** `just` (MUST NOT use make).
- **Python version:** >= 3.11

Install dev tooling and sync the venv:

    just sync          # uv sync --group dev

Lint all the things (run before committing):

    just lint          # ruff check --fix + ruff format on plugins/
    ansible-lint       # production profile, lints playbooks/, roles/, etc.
    yamlfmt            # external Go tool; format YAML files per .yamlfmt.yaml
    pre-commit run --all-files

Build the collection:

    just build         # ansible-galaxy collection build --force --output-path dist/ .

The collection has NO Python runtime dependencies. `pyproject.toml` exists
solely for dev tooling and is not a Python package (`package = false`).

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

    just sync                         # install dev tooling into venv
    just lint && ansible-lint         # lint everything
    just build                        # build collection tarball in dist/
    just clean                        # remove build artifacts and caches
    pre-commit run --all-files        # run all git hooks
