# ak1ra_lab.general

Shared Ansible collection for reusable roles, custom modules, and lookup
plugins consumed across multiple `ak1ra-lab` repositories.

Documentation: <https://ak1ra-lab.github.io/ansible-collection-general/>

## Roles

| Role | Description |
| --- | --- |
| [`apt_install`](roles/apt_install/README.md) | Add a third-party APT repository in DEB822 format with keyring, pinning, unattended upgrades, and package installation. Debian only. |
| [`debian_base`](roles/debian_base/README.md) | Apply a Debian baseline with curated packages, apt defaults, unattended upgrades, and host bootstrap settings. Debian only. |
| [`docker`](roles/docker/README.md) | Install Docker CE from the official repository and manage `daemon.json` and the `docker` group. Debian only. |
| [`go_build`](roles/go_build/README.md) | Clone and build a Go project on `localhost` and expose the built binary path. |
| [`pyproject_install`](roles/pyproject_install/README.md) | Build or install a Python package into a target virtual environment from a local wheel or an index. |

The role argument specs (`roles/<role>/meta/argument_specs.yml`) are the
canonical variable contracts; the role READMEs keep narrative and deployed
artifact details. The docs site renders the argument specs as the role
reference.

## Modules

- `github_releases_info`: query GitHub release metadata, normalize asset
  names, and select a matching asset for the local platform. Downloading is
  left to follow-up tasks such as `ansible.builtin.get_url`.
- `cpu_info`: collect CPU capability facts, including raw CPU flags and the
  detected x86-64 microarchitecture level, which can be fed into
  `github_releases_info` asset selection.

See the [module guide](https://ak1ra-lab.github.io/ansible-collection-general/modules.html)
or the [generated reference](https://ak1ra-lab.github.io/ansible-collection-general/collection_index.html)
for options, return values, and examples. The same reference is available
offline with `ansible-doc ak1ra_lab.general.<module>`.

## Lookup plugins

- `random_password`: cryptographically random password with a configurable
  length and alphabet.
- `random_base64_key`: base64-encoded random key material with a configurable
  decoded byte length.
- `random_uuid`: random RFC 4122 version 4 UUID.

See the [lookup guide](https://ak1ra-lab.github.io/ansible-collection-general/lookups.html)
for examples.

## Requirements

- Controller: `ansible-core >= 2.19.0`, Python `>= 3.11`.
- Managed nodes: Debian 12/13 for the APT-based roles.
- Collections: `ansible.posix >= 1.5.4` and `community.general >= 8.0.0`
  (resolved from [`galaxy.yml`](galaxy.yml)).
- `go` on the controller for `go_build`; `uv` for local
  `pyproject_install` builds.

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
`collections_path`. See [Getting started](https://ak1ra-lab.github.io/ansible-collection-general/getting-started.html)
for the control-node and managed-node requirements.

## Development

```shell
just sync
just all
just molecule-test
```

`just all` covers lint, mypy, unit tests, ansible-lint, docs lint, and the
docs build. `just tox-list` shows the standard tox-ansible ansible-core/Python
matrix. Molecule runs separately with an isolated container per scenario and
needs a Podman runtime (rootless works locally; CI uses rootful). See
[CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
