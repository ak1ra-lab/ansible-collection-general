# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project does not currently guarantee stable backward compatibility.

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
