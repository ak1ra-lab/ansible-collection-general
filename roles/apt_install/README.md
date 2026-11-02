# apt_install

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Adds a third-party APT repository in DEB822 format: a managed keyring, the
sources file, optional pinning and unattended-upgrades origin patterns, and
optional package installation.

Targets Debian 12/13 only (`ansible_facts['distribution'] == 'debian'`).

> For a repository-only role that never installs packages, see
> [`apt_repository`](../apt_repository/README.md). This role keeps its
> published package-installation behavior for existing consumers.

`ansible.builtin.deb822_repository` needs the `python3-debian` library on the
managed host; the role installs it before touching the repository, so minimal
installations (containers, LXC) work without extra preparation.

## Variables

The canonical variable reference is generated from `meta/argument_specs.yml` in
the collection documentation.

`apt_install_pinning: false` and `apt_install_unattended_upgrade: false` are
revert switches: the role removes a leftover file instead of writing one.

## Notes

- The role removes a legacy `/etc/apt/sources.list.d/<apt_install_repo>.list` before
  rendering the DEB822 source.
- `apt_install_dpkg_architectures` maps `ansible_facts['architecture']` to the dpkg
  architecture name used in the source file; unknown architectures are passed
  through unchanged.
