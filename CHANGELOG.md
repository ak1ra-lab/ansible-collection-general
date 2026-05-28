# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project does not currently guarantee stable backward compatibility.

## [Unreleased]

### Changed

- Renamed the Debian and Ubuntu bootstrap role from `common` to `debian_base`.
- Renamed the companion playbooks to `debian-base-defaults.yaml` and `debian-base-vps.yaml`.
- Normalized collection-internal role imports to fully qualified collection names.

### Fixed

- Updated Debian base role variables to use the `debian_base_` prefix expected by ansible-lint.
- Aligned task includes, playbooks, and role internals with current `.yaml` filenames and ansible-lint requirements.
