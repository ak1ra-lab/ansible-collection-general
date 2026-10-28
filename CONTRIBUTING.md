# Contributing

## Setup

Prerequisites: `uv`, a rootful Podman daemon (or a rootful Docker daemon),
and `go` on the controller for the `go_build` scenario.

```shell
just sync
just ansible-collection-install
just ansible-requirements-install
```

`just sync` installs the `dev` dependency group (ruff, ty, ansible-core,
pre-commit, MkDocs). `just ansible-collection-install` installs the collection
into `.ansible/collections` so FQCN role references and the modules'
`module_utils` imports resolve. `just ansible-requirements-install` installs
the collections listed in `requirements.yaml`.

The repository's `ansible.cfg` pins `roles_path=./roles` and
`collections_path=./.ansible/collections`; it does not read user-level or
parent paths.

## Checks

```shell
just lint          # ruff check --fix + ruff format over plugins/
just typecheck     # ty check over plugins/
just ansible-lint  # ansible-lint (profile: production)
just docs-lint     # antsibull-docs lint-collection-docs
just docs-build    # role coverage check + mkdocs build --strict
```

`just all` runs lint, typecheck, ansible-lint, docs lint, and the docs build.
Molecule is separate because it needs a container runtime.

Python changes under `plugins/` must pass ruff lint, ruff format, and ty.
Ansible changes must pass ansible-lint and the Molecule scenarios. Docs
changes must pass `just docs-build`.

## Testing with Molecule

Molecule scenarios live under `extensions/molecule/` (collection-testing
layout). The `default` scenario owns the shared container lifecycle
(`shared_state: true`); the component scenarios reuse the same containers and
each run prepare, converge, idempotence, verify, the scenario teardown, and a
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

# Molecule's dependency action is disabled because the shared lifecycle
# scenario runs before ansible-compat's prerun; install the collection and
# requirements explicitly as above.
just molecule-test                   # every scenario (recursive glob)
just molecule-test-one apt_install/basic
just molecule-list
```

Podman is required. Run it rootful (as the CI does): every container runs
privileged because systemd needs the capabilities. A rootful Docker daemon is
supported as an alternative; set `MOLECULE_CONTAINER_RUNTIME=docker` for every
molecule invocation. The controller additionally needs `go` (the `go_build`
scenario) and `uv` (the `pyproject_install` local scenario).

When invoking `molecule` directly instead of through the just recipes, run
`just ansible-collection-install` after editing a role or the scenario tests
the previously installed copy. Molecule caches scenario state, so a changed
`molecule.yml` needs `molecule reset` (or `destroy`).

## Documentation

The docs site is a presentation layer; it is not a second source of truth.

- Role contracts live in `roles/<role>/README.md`. The matching
  `docs/roles/<role>.md` contains only
  `--8<-- "roles/<role>/README.md"`.
- Module reference is generated from the `DOCUMENTATION`, `EXAMPLES`, and
  `RETURN` blocks in `plugins/modules/`.
- `docs/contributing.md` and `docs/changelog.md` include `CONTRIBUTING.md` and
  `CHANGELOG.md`; edit the source files.
- Hand-written pages are `docs/index.md`, `docs/installation.md`,
  `docs/architecture.md`, `docs/playbooks.md`, and `docs/modules.md`.

When adding a role:

1. Add `roles/<role>/README.md`.
2. Add the one-line `docs/roles/<role>.md` stub.
3. Add the page to the `Roles` nav section and the table in
   `docs/roles/index.md`.
4. Run `just docs-check` and `just docs-build`.

Use absolute URLs for links to repository files inside included Markdown
(role READMEs, `CHANGELOG.md`, `CONTRIBUTING.md`); a relative file link is
resolved against the docs page that includes the text and will usually break.
Anchor links inside the same role README are fine.

The site is English-only. Do not add hand-maintained translated siblings;
translate through a separate workflow if a translation is needed later.

Preview the site locally with:

```shell
just docs-serve
```

`just clean` removes the generated `site/` directory.
