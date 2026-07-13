# ak1ra_lab.general

`ak1ra_lab.general` is a shared Ansible collection for reusable roles and custom
modules consumed across multiple `ak1ra-lab` repositories.

Roles include:

- `ak1ra_lab.general.debian_base`
- `ak1ra_lab.general.go_build`
- `ak1ra_lab.general.pyproject_install`

Modules include:

- `ak1ra_lab.general.github_releases`

## Install

Create a `requirements.yaml` in the consuming repository:

```yaml
---
collections:
  - name: git+https://github.com/ak1ra-lab/ansible-collection-general.git
    version: master
```

Install into the project-local collections path:

```shell
ansible-galaxy collection install -r requirements.yaml -p ./.ansible/collections
```

This collection is intended to be consumed from `./.ansible/collections`, with
the consumer repository's `ansible.cfg` including that path at the front of
`collections_path`.

## Local Development

`ansible.cfg` sets `collections_path=./.ansible/collections` and
`roles_path=./roles` — no user-level paths are included. Install dependencies
and the collection itself before running playbooks (playbooks use FQCN roles,
so the local collection must be installed):

```shell
cp --update=none requirements.yaml requirements.dev.yaml
ansible-galaxy collection install -r requirements.dev.yaml -p ./.ansible/collections
ansible-galaxy collection install --force --collections-path .ansible/collections .
```

`requirements.dev.yaml` is git-ignored and may point to local Git repos or file
paths for in-development dependency collections.

## Roles

- `debian_base`: apply a Debian or Ubuntu baseline with curated packages, apt repository defaults, unattended upgrades, and common host bootstrap settings.
- `go_build`: clone and build a Go project on `localhost`, then expose the built binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual environment from a local wheel, PyPI, or TestPyPI.

## Modules

- `github_releases`: query GitHub release metadata, normalize asset names, select a matching asset for the local platform, and optionally download it on the managed host.

For full module argument and return-value reference, use `ansible-doc ak1ra_lab.general.github_releases`
against an installed copy of the collection.

See [docs/installation.md](docs/installation.md), [docs/roles.md](docs/roles.md), and
[docs/modules.md](docs/modules.md) for usage details.
