# ak1ra_lab.general

`ak1ra_lab.general` is a shared Ansible collection for reusable roles and custom
modules consumed across multiple `ak1ra-lab` repositories.

Roles include:

- `ak1ra_lab.general.acme_dns`
- `ak1ra_lab.general.acme_dns_register`
- `ak1ra_lab.general.apt_install`
- `ak1ra_lab.general.debian_base`
- `ak1ra_lab.general.docker`
- `ak1ra_lab.general.go_build`
- `ak1ra_lab.general.pyproject_install`

Modules include:

- `ak1ra_lab.general.github_releases_info`
- `ak1ra_lab.general.cpu_info`

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
`roles_path=./roles` - no user-level paths are included. Playbooks use FQCN
roles, so install the collection itself before running them:

```shell
ansible-galaxy collection install --force --collections-path .ansible/collections .
```

The `requirements.yaml` deps (`ansible.posix`, `community.general`) are commonly
already present at the user level, so installing the collection itself is
usually enough for local development.

## Roles

- `apt_install`: add a third-party APT repository in DEB822 format with a managed keyring, optional pinning and unattended-upgrades wiring, and optional package installation. Debian only.
- `acme_dns`: deploy an acme-dns server: Go binary built on `localhost`, systemd unit, and DNS config.
- `acme_dns_register`: register a client with an acme-dns server, persist credentials, and create `_acme-challenge` CNAME records (Cloudflare API or a manual prompt).
- `debian_base`: apply a Debian baseline with curated packages, apt repository defaults, unattended upgrades, and common host bootstrap settings. Debian only.
- `docker`: install Docker CE from the official repository and manage `/etc/docker/daemon.json` and the `docker` group. Debian only.
- `go_build`: clone and build a Go project on `localhost`, then expose the built binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual environment from a local wheel, PyPI, or TestPyPI.

## Modules

- `github_releases_info`: query GitHub release metadata, normalize asset names, and select a matching asset for the local platform. Downloading is left to follow-up tasks such as `ansible.builtin.get_url`, using the returned `download_url` and `download_checksum`.
- `cpu_info`: collect CPU capability facts, including raw CPU flags and the detected x86-64 microarchitecture level (`x86-64-v1`..`v4`), which can be fed into `github_releases_info` asset selection.

For full module argument and return-value reference, use `ansible-doc ak1ra_lab.general.github_releases_info`
against an installed copy of the collection.

See [docs/installation.md](docs/installation.md), [docs/roles.md](docs/roles.md), and
[docs/modules.md](docs/modules.md) for usage details.
