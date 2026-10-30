# ak1ra_lab.general

Shared Ansible collection for reusable roles, custom modules, and lookup
plugins consumed across multiple `ak1ra-lab` repositories.

Documentation: <https://ak1ra-lab.github.io/ansible-collection-general/>
Release notes: [CHANGELOG.rst](CHANGELOG.rst)

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

- Controller: `ansible-core >= 2.19.0`; tested with ansible-core 2.19, 2.20,
  and 2.21 (plus the weekly `devel`/`milestone` builds).
- Controller Python: `>= 3.11`; tested with Python 3.11, 3.12, and 3.13.
  ansible-core 2.20 and 2.21 additionally support Python 3.12-3.14.
- Managed nodes: Debian 12 (target Python 3.11) and Debian 13 (target Python
  3.13) for the APT-based roles. The roles use the managed node's
  `/usr/bin/python3`; no newer target interpreter is required.
- Collections: `ansible.posix >= 1.5.4` and `community.general >= 8.0.0`
  (resolved from [`galaxy.yml`](galaxy.yml)).
- `go` on the controller for `go_build`; `uv` for local
  `pyproject_install` builds.

The runtime metadata is declared in
[`meta/runtime.yml`](meta/runtime.yml), [`requirements.yml`](requirements.yml),
and [`meta/execution-environment.yml`](meta/execution-environment.yml).

## Install

Install the released collection from Ansible Galaxy:

```shell
ansible-galaxy collection install ak1ra_lab.general
```

Or pin it in a consumer `requirements.yml`:

```yaml
---
collections:
  - name: ak1ra_lab.general
    version: ">=0.4.0"
```

```shell
ansible-galaxy collection install -r requirements.yml
```

Galaxy resolves the declared `ansible.posix` and `community.general`
dependencies automatically. See [Getting started](https://ak1ra-lab.github.io/ansible-collection-general/getting-started.html)
for the control-node and managed-node requirements.

## Versioning and deprecation

The collection follows semantic versioning once it reaches `1.0.0`. Before
`1.0.0`, a minor release may contain a documented breaking change; patch
releases are limited to compatible fixes.

- Breaking changes are listed under **Breaking Changes / Porting Guide** in
  [CHANGELOG.rst](CHANGELOG.rst).
- Deprecated role variables and features are documented in the changelog and
  the role reference, and remain available for at least one minor release
  before removal. Before `1.0.0`, removal may happen in a minor release.
- Raising the minimum ansible-core or Python version is treated as a breaking
  change.
- The `galaxy.yml` version, the Git tag (`vX.Y.Z`), and the changelog release
  must match for every release.

Release order for the `ak1ra_lab` collections:

1. `ak1ra_lab.general 0.4.0`
2. `ak1ra_lab.certificate 0.1.0` (depends on general `>=0.4.0`)
3. `ak1ra_lab.network 0.4.0` (depends on general `>=0.4.0`)

## Communication

- Ansible Forum: use the [`ak1ra-lab` tag](https://forum.ansible.com/tag/ak1ra-lab)
  for questions and usage discussions.
- Bug reports and feature requests:
  <https://github.com/ak1ra-lab/ansible-collection-general/issues>
- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), which points to
  the [Ansible Community Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).

## Development

```shell
just sync
just all
just molecule-test
```

`just all` covers lint, mypy, unit tests, ansible-lint, changelog lint, docs
lint, and the docs build. `just tox-list` shows the standard tox-ansible
ansible-core/Python matrix. Molecule runs separately with an isolated
container per scenario and needs a Podman runtime (rootless works locally; CI
uses rootful). See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow
and the release checklist.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
