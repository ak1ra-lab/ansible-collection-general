---
hide:
  - toc
---

# ak1ra_lab.general

Shared Ansible collection for reusable roles and custom modules consumed across
`ak1ra-lab` repositories. It covers Debian host baselines, APT and Docker
installation, the ACME certificate workflow, Kubernetes cert-manager, and
controller-side Go and Python build helpers.

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
compose them.

- `debian_base`, `apt_install`, and `docker` establish a Debian host baseline.
- `acme_dns`, `acme_dns_register`, and `certbot` provide the DNS-01 ACME
  workflow; `cert_manager` manages cert-manager and ClusterIssuers in
  Kubernetes.
- `go_build` and `pyproject_install` build artifacts on the controller and
  install them into target environments.

Role READMEs are the source of truth for variables and deployed artifacts.
