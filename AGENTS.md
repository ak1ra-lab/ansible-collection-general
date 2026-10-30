# AGENTS.md

## Project type

This repository is the `ak1ra_lab.general` Ansible collection: a library of
reusable roles and plugins, not a consumer or a playbook project. Operational
playbooks, inventories, and helper scripts live in the separate
`ansible-playbooks-infra` repository; this collection ships no runnable
playbooks.

## Skills

Actively use the `developing-ansible` skill for Ansible work; load it before
writing or reviewing playbooks, roles, plugins, inventory, Molecule, or
collection metadata.

Prefer a user-level installation of the skill. Agents that do not have it
installed may bootstrap from
`https://raw.githubusercontent.com/ak1ra-komj/agents-skills/refs/heads/master/skills/developing-ansible/SKILL.md`;
the URL is a fallback, not the normal workflow.

## Layout

- Roles: `apt_install`, `debian_base`, `docker`, `go_build`, and
  `pyproject_install` under `roles/`.
- Modules: `github_releases_info` and `cpu_info`, with shared logic in
  `plugins/module_utils/`; lookup plugins are `random_*` under `plugins/lookup/`.
- Unit tests live in `tests/unit/`; Molecule scenarios are flat under
  `extensions/molecule/`; the Sphinx source is `docs/docsite/`.
- `apt_install` keeps its published 0.4.0 behavior. Do not add playbooks or
  operational inventories here.

## YAML and documentation

Use `.yml` for Ansible and repository YAML files. Unavoidable exceptions:

- `galaxy.yml` already uses `.yml`.
- `changelogs/config.yaml` is hardcoded by antsibull-changelog.
- `.pre-commit-config.yaml` stays `.yaml` because pre-commit 4.7 discovers only
  that name.
- Generated or upstream filenames such as `*.proxies.yaml`, `host_vars/*.yaml`,
  `50-cloud-init.yaml`, netplan files, and downloaded manifests keep their
  existing names.

`roles/<role>/meta/argument_specs.yml` is the canonical role variable
reference. Generated role docs come from argument specs; role READMEs are
concise narrative (purpose, requirements, artifacts, examples, teardown) and
must not duplicate variable tables. Module docs come from the plugin
`DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks. Never edit generated
`*_role.rst`, `*_module.rst`, or `*_lookup.rst` pages by hand.

## Tooling and validation

- Use **uv** and **just**; never `pip` or `poetry`. `just sync` installs the
  `dev` group.
- Python: **ruff** and **mypy** via `just lint` and `just typecheck`.
  `ansible-test sanity` remains the authoritative gate.
- Ansible: `just ansible-lint` (production profile) and **tox-ansible**
  (`just tox <env>`, `just unit-test`).
- Molecule: `just molecule-test`, `just molecule-test-one <scenario>`, or
  `just molecule-syntax`. Molecule installs the collection and test
  requirements itself; do not pre-install for it.
- Docs and changelog: `just docs-lint`, `just docs-build`, and
  `just changelog-lint`, using antsibull-docs/antsibull-changelog.
  `CHANGELOG.rst` is generated and must not be edited by hand.
- `just ansible-collection-install` is only for lint, mypy, and docs; the
  modules import themselves through the collection namespace.

## Workflow and safety

- Run `just all` plus the relevant Molecule scenarios before commit.
- Preserve public behavior unless the task explicitly changes it; keep changes
  consistent with the existing layout and naming.
- Do not add unpublished-dependency workarounds to CI, tests, docs, or release.
- Do not edit installed copies under `.ansible/`, `.tox/`, or `.venv/`.
- Release order: `general 0.4.0`, `certificate 0.1.0`, `network 0.4.0`; tags
  `vX.Y.Z` match `galaxy.yml`. Build and run `galaxy-importer`, then publish via
  the protected `Release` workflow only.
