---
hide:
  - toc
---

# Architecture

The collection is a set of independent roles with explicit variable contracts.
Playbooks compose the roles; the role `meta/main.yaml` files keep
`dependencies: []` so consumers control the order. A role may still use
`ansible.builtin.import_role` internally when one implementation builds on
another; those imports are part of the role contract, not a collection-wide
dependency graph.

## Role families

- **Host baseline and packages**: `debian_base`, `apt_install`, `docker`.
- **ACME and TLS**: `acme_dns`, `acme_dns_register`, `certbot`, `cert_manager`.
- **Build and install**: `go_build`, `pyproject_install`.

Each role owns its files and units. Roles do not share a global state
directory except where their READMEs document the same target path.

## Host baseline and packages

`debian_base` applies the Debian archive and security configuration,
unattended-upgrades policy, baseline packages, and optional host bootstrap
settings. `apt_install` is the reusable third-party repository layer: it
manages the keyring, a DEB822 source, optional pinning, unattended-upgrades,
and package installation or hold.

`docker` is a composition role: it imports `apt_install` for the Docker
repository, then manages `/etc/docker/daemon.json`, the `docker` group, and the
Docker service. It does not duplicate the APT repository logic.

## ACME and TLS

The ACME roles cover two different deployment shapes:

- `acme_dns` runs an acme-dns server. It builds the Go binary on the
  controller through `go_build`, deploys the binary and configuration, and
  runs the systemd service.
- `acme_dns_register` registers one acme-dns account per validation domain,
  persists the domain-to-account mapping, and creates the
  `_acme-challenge` CNAME records through the Cloudflare API or a manual
  prompt.
- `certbot` obtains and renews certificates on a systemd host. DNS-01 is the
  primary challenge type; HTTP-01 is available when the host has no DNS API
  access. The role supports apt, PyPI, and externally provided certbot
  binaries, and writes its own systemd units and timer.
- `cert_manager` is independent of the certbot roles. It installs or upgrades
  cert-manager from the official release manifest and declares ACME
  `ClusterIssuer` resources with per-issuer solvers and credentials. It does
  not create application `Ingress` or `Certificate` resources.

A typical DNS-01 flow is: deploy `acme_dns`, register client accounts and
CNAMEs with `acme_dns_register`, then configure `certbot` with the acme-dns
auth hook. The ACME roles do not call each other; the site playbook composes
them.

## Build and install

`go_build` runs on the controller by default (`hosts: localhost` in the
example playbooks). It clones a repository into a controller-local work tree,
builds a Go binary, and exposes `go_build_binary_path` for a follow-up copy or
install task. A metadata stamp makes repeated runs skip unchanged builds.

`pyproject_install` installs a Python package into a target virtual
environment. The `local` source builds a wheel on the controller with
`uv build --wheel`, copies it to the managed host, installs it with `pip`, and
removes the remote temporary wheel. The `pypi` and `testpypi` sources install
directly from an index.

`certbot` uses `pyproject_install` when `certbot_install_source: pypi`; the
import is internal to the certbot role.

## Facts and outputs

- `go_build_binary_path`, `go_build_repo_dir`, and `go_build_stamp_path` are
  exposed for follow-up tasks.
- `cpu_info` exposes `ansible_facts['cpu']`, including `flags`,
  `microarch_levels`, and `microarch_level`. `github_releases_info` accepts
  that level through `asset_microarch` when a repository publishes
  per-microarchitecture builds.

## Documentation contract

The role README is the canonical variable and artifact reference. The docs
site renders it through a one-line snippet; role-specific behavior belongs in
the README, while cross-role composition belongs in this page and in
[Playbooks](playbooks.md).
