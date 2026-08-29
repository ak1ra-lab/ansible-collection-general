# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project does not currently guarantee stable backward compatibility.

## [Unreleased]

### Added

- Added the `cpu_info` facts module, exposing CPU capability facts (`architecture`, `vendor`, `model`, `logical_cpus`, `flags`) plus the detected x86-64 microarchitecture level (`microarch_levels`, `microarch_level`).
- Added the `asset_microarch` option to `github_releases_info`, which filters out assets tagged with a different x86-64 microarchitecture level and prefers assets matching the requested level.

### Changed

- Renamed the `github_releases` module to `github_releases_info` and made it a read-only info module (`supports_check_mode`).
- Renamed the Debian and Ubuntu bootstrap role from `common` to `debian_base`.
- Renamed the companion playbooks to `debian-base-defaults.yaml` and `debian-base-vps.yaml`.
- Normalized collection-internal role imports to fully qualified collection names.

### Removed

- Removed the download options (`download`, `download_dir`, `download_mode`, `force_download`) from `github_releases_info`; the module now returns `download_url` and `download_checksum` (normalized `algorithm:value`) for direct use with `ansible.builtin.get_url`, and its playbooks perform the download.

### Fixed

- `github_releases_info` no longer reads version strings as x86-64 microarchitecture tags: `mihomo-linux-amd64-v1.19.30.deb` was previously inferred as `x86-64-v1` because of the `amd64-v1.19.30` prefix. Level tags are now only recognized when the following separator is not directly followed by a digit.
- Updated Debian base role variables to use the `debian_base_` prefix expected by ansible-lint.
- Aligned task includes, playbooks, and role internals with current `.yaml` filenames and ansible-lint requirements.
