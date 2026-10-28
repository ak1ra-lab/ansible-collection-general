# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project does not currently guarantee stable backward compatibility.

## [Unreleased]

### Added

- Add the MkDocs Material documentation site under `docs/`, rendered from the
  role READMEs and generated module reference, with `just docs-serve` and
  `just docs-build` recipes, docs linting, role coverage checks, and GitHub
  Pages publishing.

### Changed

- Split the README into a consumer landing page and `CONTRIBUTING.md`, which
  now owns the development, testing, and documentation workflow.
- Document the remaining public role variables and clarify the non-Linux
  `cpu_info` behavior in the role and module docs.

- Re-audited `debian_base_custom_sysctl_conf_entries` against the kernel
  documentation and Debian 12/13 defaults.  The example list no longer sets
  the obsolete `net.core.optmem_max=20480` (modern default 128 KiB) or the
  RAM/workload-dependent `tcp_rmem`, `tcp_wmem`, `vm.dirty_ratio` and
  `vm.dirty_background_ratio` values; the remaining entries document their
  actual trade-offs.  The list is still disabled by default, and the
  commented TCP buffer/dirty-page examples are opt-in starting points.
- `debian_base` now uses `bind9-dnsutils`, `7zip` and `gnupg` instead of the
  removed/transitional `dnsutils`, `p7zip`/`p7zip-full` and `gnupg2` package
  names; `dnsutils` has no candidate on Debian 13, so a fresh baseline install
  would fail.  The custom sshd entries now render into the role-owned
  `/etc/ssh/sshd_config.d/00-ansible-debian-base.conf` instead of editing
  `/etc/ssh/sshd_config`, disable `KbdInteractiveAuthentication` (otherwise
  PAM can still prompt for a password), validate with `sshd -t`, and notify a
  reload of `ssh.service`.  Entries are plain sshd_config lines rendered by a
  template; the old `{regexp, line}` shape is no longer used.

### Fixed

- Correct the `cpu_info` return-value reference for `flags` and remove the
  invalid `no_log` field from the `github_releases_info` `token` option
  documentation.
- `debian_base` now writes every sysctl it manages to the role-owned
  `/etc/sysctl.d/90-ansible-debian-base.conf` instead of the deprecated
  `/etc/sysctl.conf`: the TCP BBR, `net.ipv4.ip_forward` and custom sysctl
  tasks all set `ansible.posix.sysctl`'s `sysctl_file`, so the baseline has a
  stable path for auditing and host-specific `99-*` files can still override
  it by design.  The TCP BBR branch also uses the `ansible.builtin.version`
  test instead of lexicographic string comparison, so kernels such as `4.10`
  are recognized correctly.

## [0.3.0] - 2026-10-25

### Added

- Added the `certbot` role: install certbot from apt, PyPI (managed virtualenv through `pyproject_install`) or an external binary; obtain and renew certificates with DNS-01 (any `certbot-dns-*` plugin through a credentials mapping, Cloudflare by default, or acme-dns with a per-validation-domain JSON account registry and bundled manual hook) or HTTP-01 (standalone or webroot); detect domain drift in existing lineages; support external account binding (EAB, for example ZeroSSL); render global or per-lineage deploy renewal hooks, `cli.ini`, logrotate and a systemd timer. `playbooks/certbot.yaml` is the minimal example entry point.
- The `certbot` role provides `certbot_acme_ca` presets (`letsencrypt`, `zerossl`, `google`, `buypass`, `custom`), keeps `certbot_acme_server` as an explicit directory override and `certbot_staging` for Let's Encrypt staging, and manages its own systemd units under `/etc/systemd/system` for apt and PyPI installs so `certbot_bin`, the explicit paths, `certbot_renew_args` and `certbot_no_verify_ssl` stay consistent across install sources. EAB is configured through `certbot_eab`; deploy hooks can be global (`certbot_deploy_hooks`) or per lineage (`certbot_certificates[].deploy_hooks`); EAB arguments and command output are marked `no_log`. Existing lineages are not reconciled automatically: changing the CA, challenge, provider or key type needs an explicit `force: true` (or lineage deletion) to take effect. The role also validates lineage names, DNS provider names, HTTP-01 wildcards, package state and EAB values, and fails clearly when an existing certificate's SANs cannot be read.
- Added the `cert_manager` role: install/upgrade cert-manager from the official release manifest, resolving the latest stable release through `github_releases_info` when `cert_manager_version` is empty and verifying the GitHub asset digest; `cert_manager_manifest_url` and `cert_manager_manifest_checksum` override the manifest for mirrors and air-gapped installs. Manage ACME `ClusterIssuer` resources with per-issuer Cloudflare DNS-01, HTTP-01 and external account binding (EAB, for example ZeroSSL) credentials, including reference-only Secrets managed outside the role. Cloudflare and EAB credentials are modelled inside each `cert_manager_cluster_issuers[]` entry (`solver.cloudflare` and `eab`) with automatic Secret names; rendered Secret facts and manifests are marked `no_log`. It deliberately does not manage `Ingress` or `Certificate` resources, and documents the `kubernetes` Python dependency instead of creating a controller-side virtualenv.
- Added Molecule scenarios `certbot/apt` (Pebble ACME issuance over HTTP-01 with EAB and per-lineage deploy hooks), `certbot/pypi` (venv, Cloudflare plugin, credentials and units), `certbot/acmedns` (per-domain auth hook selection against a fake acme-dns API), `acme_dns_register/basic` (per-validation-domain registration and idempotence) and `cert_manager/render` (manifest rendering without a cluster, including shared and reference-only Secrets).
- `galaxy.yml` now declares `kubernetes.core`, required by `cert_manager`.

### Changed

- Rename the `acme_dns` role variable `acme_dns_domain` to `acme_dns_zone`, require `acme_dns_nsname` instead of defaulting it to the zone, and pin the built acme-dns release to `v2.0.2` with the `sqlite` database engine (the `sqlite3` engine value is removed upstream)
- Move the `acme_dns` role's upstream build identity and systemd service/unit names from defaults to internal role vars; `acme_dns_go_build_repo_version`, `_goarch`, and `_base_dir` remain overridable
- Keep `acme_dns_group` as a separate service group defaulting to `acme-dns`, and derive the default home/config directories from `acme_dns_user`
- `acme_dns_register` now registers one acme-dns account per validation domain, persists a domain -> account mapping to `acme_dns_credentials.yaml`, creates each `_acme-challenge` CNAME against that domain's own fulldomain, and supports per-domain Cloudflare zone overrides; the single-account `acme_dns_register_username` / `_password` / `_subdomain` / `_fulldomain` interface is removed.

### Fixed

- Strip trailing dots from the `acme_dns` role's `acme_dns_zone` and `acme_dns_nsname`; acme-dns appends the root label itself, so the previous template produced invalid `..` names and silently started without its SOA and static records
- Stop writing an A record in the `acme_dns` role for an out-of-zone `acme_dns_nsname`; that address belongs in the parent zone. The role's README now separates parent-zone delegation records from the records served by acme-dns
- `acme_dns_register` keeps its resolved server URL and account registry in internal `_acme_dns_register_*` facts and publishes `acme_dns_register_effective_*` outputs. Values passed as `include_role`/`import_role` `vars:` outrank `set_fact`, so the previous code updated facts that the role itself could not see: after a successful registration its validation still read the original empty registry and failed.
- `acme_dns_register` keeps explicitly loading `acme_dns_credentials.yaml`, including from the default `host_vars/<inventory_hostname>/` directory: role parameters outrank Ansible's auto-loaded host_vars, so the explicit include is what keeps role-parameter invocations idempotent.
- `acme_dns_register` no longer asks the operator to add CNAME records with a literal `*.` label for wildcard domains.
- `acme_dns_register` escapes the Cloudflare zone in the CNAME record regex.
- `acme_dns_register` marks the Cloudflare token fact and API task `no_log` so API tokens stay out of verbose output.
- `go_build` resolves the checkout, working directory, binary and stamp paths in internal facts and publishes them after the build, so `go_build_repo_dir` and `go_build_chdir` passed as role parameters are no longer shadowed by `set_fact`.
- `debian_base` appends the backports suite in the repository task instead of mutating `debian_base_apt_repo_debian_suites` with `set_fact`, so a caller-provided suite list passed as a role parameter still receives the backports suite.
- `debian_base` refreshes the APT index after adding the backports source, so enabling backports is idempotent: the first run already upgrades backports packages (for example `linux-libc-dev`) instead of leaving them for a later run.
- Use bare Jinja2 builtin filter and test names (`lower`, `trim`, `sequence`, `string`, `mapping`, `defined`, `boolean`, `equalto`, ...) instead of `ansible.builtin.*`: the fully-qualified aliases only exist in ansible-core 2.19+, while the collection still declares 2.18 as its minimum.

## [0.2.0] - 2026-10-14

### Added

- Added the `asset_microarch` option to `github_releases_info`, which filters out assets tagged with a different x86-64 microarchitecture level and prefers assets matching the requested level.
- Added Molecule scenarios under `extensions/molecule/` (`apt_install/basic`, `apt_install/variants`, `debian_base`, `go_build`, `pyproject_install/local`, `pyproject_install/pypi`) with a shared, runtime-selectable container lifecycle (Debian 12/13), justfile recipes, and a GitHub Actions lint + Molecule workflow with Dependabot updates for the pinned actions.

### Changed

- Renamed the `github_releases` module to `github_releases_info` and made it a read-only info module (`supports_check_mode`).
- Documented the `apt_install` and `docker` roles (per-role README and role metadata); the collection's APT-based roles now state Debian-only platform support.
- Added role metadata (`meta/main.yaml`) and READMEs for every role.
- `galaxy.yml` declares the runtime collection dependencies (`ansible.posix`, `community.general`) and drops the stale `roles/*/molecule` manifest directive.
- Simplified `.ansible-lint` to `profile`, `exclude_paths` and `skip_list`;
  dropping the explicit `kinds:` mapping restores the default kind detection,
  which had been silently disabling `var-naming[no-role-prefix]` for role
  defaults (and lints the Molecule playbooks as playbooks again).
- Adopted the ruff default rule set (`ruff >= 0.17`, line length 120): the
  plugin Python now uses PEP 585/604 annotations (with `from __future__ import
  annotations` for older managed-node interpreters) and f-strings; the
  pre-commit ruff hook tracks the same version.
- Renamed the `apt_install` role variables to the `apt_install_*` role prefix
  (`apt_repo` → `apt_install_repo`, `apt_keyrings_*` →
  `apt_install_keyrings_*`, `apt_pinning*` → `apt_install_pinning*`,
  `apt_unattended_upgrade*` → `apt_install_unattended_upgrade*`,
  `apt_mark_hold` → `apt_install_mark_hold`, `dpkg_architectures` →
  `apt_install_dpkg_architectures`), updating the `docker` role, the
  `playbooks/apt_install/` examples and the Molecule scenarios. Consuming
  playbooks must rename the variables accordingly.

### Removed

- Removed the mkdocs documentation site (`docs/`, `mkdocs.yml`, the GitHub Pages workflow and the `docs` dependency group): the root README, the per-role `roles/<role>/README.md` files and the module `DOCUMENTATION` blocks are the single source of truth.
- Removed the `ansible-collection-build` justfile recipe.
- Removed the download options (`download`, `download_dir`, `download_mode`, `force_download`) from `github_releases_info`; the module now returns `download_url` and `download_checksum` (normalized `algorithm:value`) for direct use with `ansible.builtin.get_url`, and its playbooks perform the download.

### Fixed

- `github_releases_info` no longer reads version strings as x86-64 microarchitecture tags: `mihomo-linux-amd64-v1.19.30.deb` was previously inferred as `x86-64-v1` because of the `amd64-v1.19.30` prefix. Level tags are now only recognized when the following separator is not directly followed by a digit.
- `apt_install` now installs `python3-debian` before using `ansible.builtin.deb822_repository`, so minimal Debian installations no longer fail on the missing library.
- `apt_install` refreshes the APT index whenever the source configuration changes, so a fresh-but-stale cache can no longer hide the repository that was just added; repeat runs stay idempotent.
- `debian_base` fails fast on non-Debian hosts instead of rendering Debian archive and security repositories on Ubuntu.
- `acme_dns_register` marks credential handling (`POST /register`, credential facts, credentials file) as `no_log` so passwords stay out of verbose output and diffs.

## [0.1.0] - 2026-08-29

Initial release of the `ak1ra_lab.general` collection: the reusable roles
`acme_dns`, `acme_dns_register`, `apt_install`, `debian_base`, `docker`,
`go_build` and `pyproject_install` with their companion playbooks, the
`github_releases` and `cpu_info` modules, and the bilingual mkdocs
documentation site.

### Added

- Added the `cpu_info` facts module, exposing CPU capability facts (`architecture`, `vendor`, `model`, `logical_cpus`, `flags`) plus the detected x86-64 microarchitecture level (`microarch_levels`, `microarch_level`).

### Changed

- Renamed the Debian and Ubuntu bootstrap role from `common` to `debian_base`.
- Renamed the companion playbooks to `debian-base-defaults.yaml` and `debian-base-vps.yaml`.
- Normalized collection-internal role imports to fully qualified collection names.

### Fixed

- Updated Debian base role variables to use the `debian_base_` prefix expected by ansible-lint.
- Aligned task includes, playbooks, and role internals with current `.yaml` filenames and ansible-lint requirements.
