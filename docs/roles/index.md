---
hide:
  - toc
---

# Roles

Each page below is the canonical `roles/<role>/README.md`, included in the
docs site from the role directory. Edit the role README, not this index, when
the contract changes.

| Role | Description |
| --- | --- |
| [`apt_install`](apt_install.md) | Add a third-party APT repository in DEB822 format with keyring, pinning, unattended upgrades, and package installation. |
| [`debian_base`](debian_base.md) | Apply a Debian baseline with curated packages, apt defaults, unattended upgrades, and host bootstrap settings. |
| [`docker`](docker.md) | Install Docker CE from the official repository and manage `daemon.json` and the `docker` group. |
| [`go_build`](go_build.md) | Clone and build a Go project on `localhost` and expose the built binary path. |
| [`pyproject_install`](pyproject_install.md) | Build or install a Python package into a target virtual environment from a local wheel or an index. |

## Role families

- Host baseline and packages: `debian_base`, `apt_install`, `docker`.
- Build and install: `go_build`, `pyproject_install`.

See [Architecture](../architecture.md) for how the families compose.
