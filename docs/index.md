---
hide:
  - toc
---

# ak1ra_lab.general

Shared Ansible collection for reusable roles, modules, and lookup plugins
consumed across `ak1ra-lab` repositories. It covers Debian host baselines,
APT and Docker installation, and controller-side Go and Python build helpers.

## Start here

- [Getting started](installation.md) - install the collection and prepare the
  control and managed nodes.
- [Architecture](architecture.md) - how the role families fit together.
- [Playbooks](playbooks.md) - bundled entry points and example invocations.
- [Roles](roles/index.md) - the canonical role contracts.
- [Modules](modules.md) - GitHub release selection and CPU capability facts.
- [Module reference](ak1ra_lab.general/index.md) - generated from the
  in-code documentation.
- [Contributing](contributing.md) - development, testing, and docs workflow.
- [Changelog](changelog.md) - release history.

!!! note "Source of truth"
    Role documentation lives in each role's `README.md` and is rendered in the
    Roles section. Module reference is generated from the `DOCUMENTATION`,
    `EXAMPLES`, and `RETURN` blocks in `plugins/modules/`. Edit those sources,
    not the generated site.

## Design at a glance

The collection is a set of roles with explicit variable contracts; playbooks
compose them, and a few roles use another role internally for implementation.

- `debian_base`, `apt_install`, and `docker` establish a Debian host baseline.
- `go_build` and `pyproject_install` build artifacts on the controller and
  install them into target environments.
- `random_password`, `random_base64_key`, and `random_uuid` generate
  controller-side secrets for composed playbooks.

Role READMEs are the source of truth for variables and deployed artifacts.
