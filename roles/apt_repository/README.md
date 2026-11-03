# apt_repository

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Manages one third-party APT repository without installing its packages: an
optional keyring, a DEB822 source, optional pinning, and optional
unattended-upgrades origins.

Targets Debian 12/13 and Ubuntu 22.04 and later. Ubuntu 24.04 and 26.04 are
the tested Ubuntu releases.

## Deployed artifacts

- Keyring at the path from `apt_repository_keyring.dest`, or an external
  `apt_repository_signed_by` reference.
- `/etc/apt/sources.list.d/<name>.sources` through
  `ansible.builtin.deb822_repository`.
- Optional `/etc/apt/preferences.d/90<name>` through `apt_preference`.
- Optional `/etc/apt/apt.conf.d/90unattended-upgrades-<name>` through
  `apt_unattended_upgrades`.
- Legacy `/etc/apt/sources.list.d/<name>.list` cleanup.

## What it does not do

- It does not install packages from the configured repository, even keyring
  packages. Use the `deb` + `member` keyring source to extract a keyring from
  a package without installing it.
- It does not run `apt-mark hold`. Manage holds in the playbook after the
  package installation.

`ansible.builtin.deb822_repository` requires the `python3-debian` library on
the managed host. The role installs it from the existing base repositories,
because it is a module dependency rather than a package from the configured
repository. This does not install anything provided by the new repository.

## Keyring sources

Exactly one of `url`, `content`, `content_base64`, and `deb` is used when
installing a keyring from `apt_repository_keyring`.

`deb` requires `member`, the path of the keyring inside the package. For
example, the deb-multimedia keyring package contains both a global
`trusted.gpg.d` copy and a `Signed-By`-oriented copy:

```yaml
apt_repository_keyring:
  deb: https://www.deb-multimedia.org/pool/main/d/deb-multimedia-keyring/deb-multimedia-keyring_2024.9.1_all.deb
  member: usr/share/keyrings/deb-multimedia-keyring.pgp
  checksum: "sha256:8dc6cbb266c701cfe58bd1d2eb9fe2245a1d6341c7110cfbfe3a5a975dcf97ca"
  dest: /etc/apt/keyrings/deb-multimedia.gpg
```

The role extracts only the requested member; it does not add the package to
the dpkg database or install the global `trusted.gpg.d` key.

## Keyring download proxy and retries

Set `apt_repository_download_proxy` (and optionally
`apt_repository_download_no_proxy`) when the keyring download needs a proxy:

```yaml
apt_repository_download_proxy: http://proxy.example:3128
apt_repository_download_no_proxy: localhost,127.0.0.1,.internal
```

The role passes these values to the keyring task's environment. Timeout and
retry behavior are controlled by `apt_repository_keyring_timeout`,
`apt_repository_keyring_retries`, and `apt_repository_keyring_retry_delay`.
Set a checksum on `apt_repository_keyring` when the source publishes one, so a
truncated download is rejected instead of installed.

## Pinning and unattended upgrades

Both features are opt-in. An empty `apt_repository_pinning` list and an empty
`apt_repository_unattended_upgrades` dictionary disable them and remove a
stale role-owned file.

`apt_preference` normalizes full release field names such as `origin` and
`codename` to the single-letter fields APT understands in `Pin: release`.
`apt_unattended_upgrades` accepts the full names and emits them as-is.

`Pin: origin` matches a repository hostname and is configured through
`pin.site`; it is not the same as the Release file's `Origin:` field.

## Example

```yaml
- name: add the PostgreSQL PGDG repository
  ansible.builtin.include_role:
    name: ak1ra_lab.general.apt_repository
  vars:
    apt_repository_name: pgdg
    apt_repository_uris:
      - https://apt.postgresql.org/pub/repos/apt
    apt_repository_suites:
      - "{{ ansible_facts['distribution_release'] }}-pgdg"
    apt_repository_components:
      - main
    apt_repository_keyring:
      url: https://www.postgresql.org/media/keys/ACCC4CF8.asc
      dest: /etc/apt/keyrings/postgresql-pgdg.asc
    apt_repository_pinning:
      - packages: ["postgresql-*", "postgresql-common"]
        pin:
          release:
            origin: apt.postgresql.org
            codename: "{{ ansible_facts['distribution_release'] }}-pgdg"
        priority: 900
    apt_repository_unattended_upgrades:
      origins_patterns:
        - origin: apt.postgresql.org
          codename: "{{ ansible_facts['distribution_release'] }}-pgdg"
```

Then install packages and set holds in the playbook:

```yaml
- name: install a package from the new repository
  ansible.builtin.apt:
    name: postgresql-17
    state: present
    update_cache: true

- name: hold the package
  ansible.builtin.dpkg_selections:
    name: postgresql-17
    selection: hold
```

## Notes

- Ubuntu PPA sources are intentionally not implemented. Use
  `add-apt-repository` / `software-properties-common` for PPAs; this role is
  for vendor repositories whose key and DEB822 source you control.
- `apt_preference` writes files that APT parses in alphanumeric order. Keep
  the `90` prefix unless you have a reason to order differently.
- The role refreshes the APT index only when repository artifacts change. It
  never upgrades or installs a package.
