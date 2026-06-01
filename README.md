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

When validating this collection from its own repository, refresh the repo-local
installed copy before running `ansible-lint`, `ansible-playbook`, or other
commands that resolve `ak1ra_lab.general.*` from `./.ansible/collections`:

```shell
just install
```

This wraps `ansible-galaxy collection install --upgrade --collections-path
.ansible/collections .` from the repository root so the installed copy matches
the working tree.

Do not create a symlink at
`./.ansible/collections/ansible_collections/ak1ra_lab/general` inside this
repository. That shortcut can interfere with `ansible-lint` and
`ansible-galaxy collection build`.

For cross-repository local development, install directly from the source
checkout into the consumer repository:

```shell
ansible-galaxy collection install /path/to/ansible-collection-general -p ./.ansible/collections --force
```

Re-run the install after source changes so the consumer repository sees the
updated collection content.

## Roles

- `debian_base`: apply a Debian or Ubuntu baseline with curated packages, apt repository defaults, unattended upgrades, and common host bootstrap settings.
- `go_build`: clone and build a Go project on `localhost`, then expose the built binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual environment from a local wheel, PyPI, or TestPyPI.

See [docs/installation.md](docs/installation.md) and [docs/roles.md](docs/roles.md)
for usage details.
