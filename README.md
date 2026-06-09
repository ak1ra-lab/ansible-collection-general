# ak1ra_lab.general

`ak1ra_lab.general` is a shared Ansible collection for reusable roles that are
consumed across multiple `ak1ra-lab` repositories.

Roles include:

- `ak1ra_lab.general.debian_base`
- `ak1ra_lab.general.go_build`
- `ak1ra_lab.general.pyproject_install`

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

This repository is structured to sit inside an `ansible_collections/ak1ra_lab/`
directory tree. The `ansible.cfg` sets `collections_path=../../../../collections`
so Ansible resolves `ak1ra_lab.*` namespaces directly from the surrounding checkout
tree without any additional install step.

## Roles

- `debian_base`: apply a Debian or Ubuntu baseline with curated packages, apt repository defaults, unattended upgrades, and common host bootstrap settings.
- `go_build`: clone and build a Go project on `localhost`, then expose the built binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual environment from a local wheel, PyPI, or TestPyPI.

See [docs/installation.md](docs/installation.md) and [docs/roles.md](docs/roles.md)
for usage details.
