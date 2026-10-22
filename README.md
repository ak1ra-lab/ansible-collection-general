# ak1ra_lab.general

`ak1ra_lab.general` is a shared Ansible collection for reusable roles and custom
modules consumed across multiple `ak1ra-lab` repositories.

Roles include:

- `ak1ra_lab.general.acme_dns`
- `ak1ra_lab.general.acme_dns_register`
- `ak1ra_lab.general.apt_install`
- `ak1ra_lab.general.cert_manager`
- `ak1ra_lab.general.certbot`
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

## Testing

Molecule scenarios live under `extensions/molecule/` (collection-testing
layout). The `default` scenario owns the shared container lifecycle
(`shared_state: true`); the component scenarios reuse the same containers and
each run prepare, converge, idempotence, verify, the scenario teardown and a
teardown verification.

| Scenario | Coverage |
| --- | --- |
| `apt_install/basic` | Third-party repository keyring URL, DEB822 source, origin pinning, unattended-upgrades, package install and hold, the revert switches, legacy `.list` removal |
| `apt_install/variants` | Inline keyring content, release-based pinning, `any-version` suites, a keyring package with a pinned checksum |
| `cert_manager/render` | ClusterIssuer/Secret rendering, per-issuer Cloudflare and HTTP-01 solvers, EAB, shared/reference-only Secrets, manifest permissions (no cluster required) |
| `certbot/apt` | apt install, Pebble ACME issuance via HTTP-01 with EAB, renewal configuration, role-managed unit, per-lineage deploy hook dispatch and timer |
| `certbot/pypi` | PyPI install into the managed venv, Cloudflare plugin, credentials, hook, cli.ini, logrotate and systemd units |
| `certbot/acmedns` | per-validation-domain acme-dns auth hook selection against a fake `/update` API |
| `acme_dns_register/basic` | per-validation-domain acme-dns registration, mapping persistence and idempotence against a fake `/register` API |
| `debian_base` | DEB822 archive/security sources, backports pinning and first-run index refresh, unattended-upgrades drop-ins, force-IPv4, baseline package, sudoers |
| `go_build` | Fixture git repository, binary build and stamp-based rebuild skip |
| `pyproject_install/local` | `uv build --wheel` on the controller, wheel install into the target venv, remote wheel cleanup |
| `pyproject_install/pypi` | PyPI install into a target venv, role-provided system packages |

The managed nodes are the Debian 12/13 systemd images from
[ak1ra-lab/docker-systemd](https://github.com/ak1ra-lab/docker-systemd); the
APT-based roles are Debian-only by contract.

```shell
# First run only: the scenarios search the project-local collections path
# (ANSIBLE_COLLECTIONS_PATH in extensions/molecule/config.yml), and the
# default scenario creates the shared containers before Molecule installs
# anything itself.
just ansible-collection-install
just ansible-requirements-install

just molecule-test                   # every scenario (recursive glob)
just molecule-test-one apt_install/basic
just molecule-list
```

Podman is required. Run it rootful (as the CI does): every container runs
privileged because systemd needs the capabilities. A rootful Docker daemon is
supported as an alternative - set `MOLECULE_CONTAINER_RUNTIME=docker` for
every molecule invocation. The controller additionally needs `go` (the
`go_build` scenario) and `uv` (the `pyproject_install` local scenario).

## Roles

- `acme_dns`: deploy an acme-dns server: Go binary built on `localhost`, systemd unit, and DNS config.
- `acme_dns_register`: register one acme-dns account per validation domain, persist the domain -> account mapping, and create each `_acme-challenge` CNAME record against that domain's own fulldomain (Cloudflare API or a manual prompt).
- `apt_install`: add a third-party APT repository in DEB822 format with a managed keyring, optional pinning and unattended-upgrades wiring, and optional package installation. Debian only.
- `cert_manager`: install/upgrade cert-manager from the official release manifest (latest stable by default, resolved through `github_releases_info`) and declare ACME `ClusterIssuer` resources with per-issuer Cloudflare DNS-01, HTTP-01 and external account binding (EAB, for example ZeroSSL) credentials, including reference-only Secrets. Application `Ingress`/`Certificate` resources are intentionally out of scope.
- `certbot`: obtain and renew certificates with certbot from apt or a managed PyPI virtualenv, using DNS-01 (Cloudflare, or acme-dns with one account per validation domain) or HTTP-01, with EAB support, global or per-lineage renewal deploy hooks and a systemd timer.
- `debian_base`: apply a Debian baseline with curated packages, apt repository defaults, unattended upgrades, and common host bootstrap settings. Debian only.
- `docker`: install Docker CE from the official repository and manage `/etc/docker/daemon.json` and the `docker` group. Debian only.
- `go_build`: clone and build a Go project on `localhost`, then expose the built binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual environment from a local wheel, PyPI, or TestPyPI.

## Modules

- `github_releases_info`: query GitHub release metadata, normalize asset names, and select a matching asset for the local platform. Downloading is left to follow-up tasks such as `ansible.builtin.get_url`, using the returned `download_url` and `download_checksum`.
- `cpu_info`: collect CPU capability facts, including raw CPU flags and the detected x86-64 microarchitecture level (`x86-64-v1`..`v4`), which can be fed into `github_releases_info` asset selection.

For full module argument and return-value reference, use `ansible-doc ak1ra_lab.general.github_releases_info`
against an installed copy of the collection; `playbooks/github_releases/inspect-latest.yaml` inspects a
release (and the selected asset) without downloading.

Facts from third-party collections are not part of `ansible.builtin.setup`: run
`ak1ra_lab.general.cpu_info` explicitly in the play and feed
`ansible_facts['cpu']['microarch_level']` into `asset_microarch` when a repository publishes
per-level builds. Each role's variables and outcomes are documented in its
`roles/<role>/README.md`.
