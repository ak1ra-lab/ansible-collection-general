# Contributing

## Setup

Prerequisites: `uv`, a Podman daemon (rootless is enough; CI uses rootful),
and `go` on the controller for the `go_build` scenario.

```shell
just sync
just ansible-collection-install
```

`just sync` installs the `dev` dependency group (ruff, mypy, ansible-core,
ansible-lint, tox-ansible, Molecule, pre-commit, MkDocs).
`just ansible-collection-install` installs the collection into
`.ansible/collections` so FQCN role references and the modules' `module_utils`
imports resolve for lint, mypy, and docs. Molecule does **not** use that copy:
it installs the collection under test itself and reads its test collection
requirements from `tests/molecule/requirements.yml`.

The repository's `ansible.cfg` pins `roles_path=./roles` and
`collections_path=./.ansible/collections`; it does not read user-level or
parent paths.

## Checks

```shell
just lint          # ruff check --fix + ruff format over plugins/ and tests/
just typecheck     # mypy over plugins/ and tests/
just unit-test     # ansible-test units in the tox-ansible unit-py3.13-2.21 env
just tox-list      # show the tox-ansible ansible-core/Python matrix
just ansible-lint  # ansible-lint (profile: production)
just docs-lint     # antsibull-docs lint-collection-docs
just docs-build    # role coverage check + mkdocs build --strict
```

`just all` runs lint, typecheck, unit tests, ansible-lint, docs lint, and the
docs build. Molecule is separate because it needs a container runtime.

Run one matrix entry with `just tox sanity-py3.13-2.21` (or any environment
shown by `just tox-list`). `ansible-test sanity` is the authoritative
Ansible/Python gate; mypy is the fast local typecheck. The matrix follows
ansible-core 2.19/2.20/2.21 plus the weekly devel/milestone environments, and
`tox-ansible` installs test collections from `tests/molecule/requirements.yml`
through `ade` - do not pre-install them into `.ansible/collections`.

Python changes under `plugins/` and `tests/` must pass ruff lint, ruff format,
mypy, and the unit tests. Ansible changes must pass ansible-lint and the
Molecule scenarios. Docs changes must pass `just docs-build`.

## Testing with Molecule

Molecule scenarios live flat under `extensions/molecule/<name>/`. Each
scenario owns its containers: the shared `create.yml`/`destroy.yml` playbooks
build names from the scenario name and a checkout hash, so scenarios and
parallel checkouts cannot collide. There is no shared `default` lifecycle
scenario and no `shared_state`.

| Scenario | Coverage |
| --- | --- |
| `apt_install_basic` | Third-party repository keyring URL, DEB822 source, origin pinning, unattended-upgrades, package install and hold, the revert switches, legacy `.list` removal |
| `apt_install_variants` | Inline keyring content, release-based pinning, `any-version` suites, a keyring package with a pinned checksum |
| `debian_base` | DEB822 archive/security sources, backports pinning and first-run index refresh, unattended-upgrades drop-ins, force-IPv4, baseline package, sudoers |
| `go_build` | Fixture git repository, binary build and stamp-based rebuild skip |
| `pyproject_install_local` | `uv build --wheel` on the controller, wheel install into the target venv, remote wheel cleanup |
| `pyproject_install_pypi` | PyPI install into a target venv, role-provided system packages |

The managed nodes are the Debian 12/13 systemd images from
[ak1ra-lab/docker-systemd](https://github.com/ak1ra-lab/docker-systemd); the
APT-based roles are Debian-only by contract.

```shell
just molecule-test                   # every scenario
just molecule-test-one apt_install_basic
just molecule-syntax                 # syntax-check converge playbooks
just molecule-list
```

Molecule's dependency action installs `tests/molecule/requirements.yml`
(`containers.podman`, `community.docker`); ansible-compat's prerun installs
the collection under test and its `galaxy.yml` dependencies. Do not pre-install
the collection or test collections into `.ansible/collections` for Molecule.

Podman is required. Rootless Podman works for the whole general suite; CI uses
rootful Podman for a uniform systemd container runtime. A Docker daemon is
supported as an alternative; set `MOLECULE_CONTAINER_RUNTIME=docker` for every
molecule invocation. The controller additionally needs `go` (the `go_build`
scenario) and `uv` (the `pyproject_install` local scenario).

Molecule caches scenario state, so a changed `molecule.yml` needs
`molecule reset` (or `destroy`).

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
