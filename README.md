# ak1ra_lab.general

Shared Ansible collection for reusable roles and custom modules consumed across
multiple `ak1ra-lab` repositories.

Documentation: <https://ak1ra-lab.github.io/ansible-collection-general/>

## Roles

| Role | Description |
| --- | --- |
| [`acme_dns`](roles/acme_dns/README.md) | Deploy an acme-dns server with the Go binary built on the controller and a systemd service. |
| [`acme_dns_register`](roles/acme_dns_register/README.md) | Register one acme-dns account per validation domain and create `_acme-challenge` CNAMEs. |
| [`apt_install`](roles/apt_install/README.md) | Add a third-party APT repository in DEB822 format with keyring, pinning, unattended upgrades, and package installation. Debian only. |
| [`certbot`](roles/certbot/README.md) | Obtain and renew certificates with certbot from apt, PyPI, or an external binary. |
| [`cert_manager`](roles/cert_manager/README.md) | Install cert-manager and declare ACME `ClusterIssuer` resources with per-issuer solvers. |
| [`debian_base`](roles/debian_base/README.md) | Apply a Debian baseline with curated packages, apt defaults, unattended upgrades, and host bootstrap settings. Debian only. |
| [`docker`](roles/docker/README.md) | Install Docker CE from the official repository and manage `daemon.json` and the `docker` group. Debian only. |
| [`go_build`](roles/go_build/README.md) | Clone and build a Go project on `localhost` and expose the built binary path. |
| [`pyproject_install`](roles/pyproject_install/README.md) | Build or install a Python package into a target virtual environment from a local wheel or an index. |

The role READMEs are the canonical variable contracts. The docs site renders
them as the role reference.

## Modules

- `github_releases_info`: query GitHub release metadata, normalize asset
  names, and select a matching asset for the local platform. Downloading is
  left to follow-up tasks such as `ansible.builtin.get_url`.
- `cpu_info`: collect CPU capability facts, including raw CPU flags and the
  detected x86-64 microarchitecture level, which can be fed into
  `github_releases_info` asset selection.

See the [module guide](https://ak1ra-lab.github.io/ansible-collection-general/modules/)
or the [generated reference](https://ak1ra-lab.github.io/ansible-collection-general/ak1ra_lab.general/)
for options, return values, and examples. The same reference is available
offline with `ansible-doc ak1ra_lab.general.<module>`.

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
`collections_path`. See [Getting started](https://ak1ra-lab.github.io/ansible-collection-general/installation/)
for the control-node and managed-node requirements.

## Development

```shell
just sync
just all
just molecule-test
```

`just all` covers lint, typecheck, ansible-lint, docs lint, and the docs build.
Molecule needs a rootful container runtime and is run separately. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## License

MIT. See [LICENSE](LICENSE).
