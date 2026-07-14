# ak1ra_lab.general

`ak1ra_lab.general` is a shared Ansible collection of reusable roles and custom
modules consumed across multiple `ak1ra-lab` repositories.

## Roles

- `debian_base`: apply a Debian or Ubuntu baseline with curated packages, apt
  repository defaults, unattended upgrades, and common host bootstrap settings.
- `go_build`: clone and build a Go project on `localhost`, then expose the built
  binary path for follow-up tasks.
- `pyproject_install`: build or install a Python package into a target virtual
  environment from a local wheel, PyPI, or TestPyPI.

## Modules

- `github_releases`: query GitHub release metadata, normalize asset names, select
  a matching asset for the local platform, and optionally download it on the
  managed host.

See [Installation](installation.md), [Roles](roles.md), and
[Modules](modules.md) for usage details.
