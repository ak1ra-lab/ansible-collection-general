# ak1ra_lab.general

`ak1ra_lab.general` is a shared Ansible collection for reusable roles that are
consumed across multiple `ak1ra-lab` repositories.

Initial roles:

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

For editable local development across repositories, either install directly from
the source checkout:

```shell
ansible-galaxy collection install /path/to/ansible-collection-general -p ./.ansible/collections --force
```

or create a symlink under `./.ansible/collections/ansible_collections/ak1ra_lab/general`
that points at this repository root.

## Roles

- `go_build`: clone and build a Go project on `localhost`, then expose the built binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual environment from a local wheel, PyPI, or TestPyPI.

See [docs/installation.md](docs/installation.md) and [docs/roles.md](docs/roles.md)
for usage details.
