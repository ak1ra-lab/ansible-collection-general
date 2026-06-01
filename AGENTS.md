# AGENTS.md

This project is under active development. Refactor without any concern for backward compatibility.

## What This Project Does

`ak1ra_lab.general` is a shared Ansible collection for reusable roles and playbooks
consumed across multiple `ak1ra-lab` repositories. The repository is
Ansible-only and currently centers on Debian or Ubuntu bootstrap, package
repository management, and local build or install helpers. See `README.md` for
consumer installation and role usage details.

## Environment & Tooling - CRITICAL

- MUST work from the repository root so `ansible.cfg` keeps
  `collections_path=./.ansible/collections` in effect.
- MUST run `just install` before validating repo-local playbooks, FQCN role
  imports, or any change that depends on collection resolution from
  `./.ansible/collections`.
- MUST run `ansible-lint` after changes under `playbooks/`, `roles/`, `meta/`,
  `galaxy.yml`, or `.ansible-lint`.
- MUST run `ansible-playbook --syntax-check <playbook>` for each touched
  top-level playbook.
- MUST use the checked-in `justfile` for routine commands when a recipe exists.
- MUST use `just build` when validating collection packaging changes.
- MUST NOT create or rely on a symlink at
  `./.ansible/collections/ansible_collections/ak1ra_lab/general` inside this
  repository.
- MUST NOT validate against a stale installed copy under
  `./.ansible/collections/ansible_collections/ak1ra_lab/general`.

## Conventions

- Role imports MUST use FQCN: `ak1ra_lab.general.<role>`.
- Role-owned variables MUST use the role prefix, such as `debian_base_*`,
  `apt_install_*`, and `docker_*`.
- New caller-overridable values MUST live in `roles/<role>/defaults/main.yaml`.
- `galaxy.yml` is the source of truth for collection metadata.
- `ansible.cfg` is the source of truth for local role and collection resolution.
- YAML files MUST use the `.yaml` extension, and Ansible modules SHOULD use
  FQCNs.

## Testing Guidelines

- There is currently no repo-local `src/` or `tests/` tree; this repository's
  validation workflow is Ansible-only.
- Treat `ansible-lint` plus targeted `ansible-playbook --syntax-check` runs as
  the required validation baseline.
- If you rename a role, variable prefix, or playbook filename, update every
  affected playbook and role-to-role import in the same change.
- Do not rely on live infrastructure runs unless the user explicitly asks for
  runtime validation.

## Common Operations

```shell
just install                                # refresh the repo-local installed collection copy
ansible-lint                                # lint collection Ansible content
ansible-playbook --syntax-check playbooks/debian-base-defaults.yaml
ansible-playbook --syntax-check playbooks/docker-defaults.yaml
just build                                  # build a collection artifact under dist/
git status --short                          # inspect pending changes before staging
```
