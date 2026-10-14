# apt_install

Adds a third-party APT repository in DEB822 format: a managed keyring, the
sources file, optional pinning and unattended-upgrades origin patterns, and
optional package installation.

Targets Debian 12/13 only (`ansible_facts['distribution'] == 'debian'`).

`ansible.builtin.deb822_repository` needs the `python3-debian` library on the
managed host; the role installs it before touching the repository, so minimal
installations (containers, LXC) work without extra preparation.

## Required Variables

- `apt_install_repo` - repository name; used for the `sources.list.d` file name, the
  pinning file name (`/etc/apt/preferences.d/90<repo>`), the
  unattended-upgrades file name, and the legacy `<repo>.list` removal.
- `apt_install_repo_uris` - repository URI(s); a string or a list of strings.
- `apt_install_keyrings_dest` - destination path of the imported keyring, e.g.
  `/etc/apt/keyrings/example.asc` (armored) or `.../example.gpg` (binary).
- exactly one of:
  - `apt_install_keyrings_url` - downloaded with `ansible.builtin.get_url`
  - `apt_install_keyrings_file` - copied from the **controller** with `ansible.builtin.copy`
  - `apt_install_keyrings_content` - inline material written with `ansible.builtin.copy`
  - `apt_install_keyrings_package` - `.deb` downloaded (with optional
    `apt_install_keyrings_package_checksum`) and installed as a keyring package

## Common Variables

| Variable | Default | Description |
| --- | --- | --- |
| `apt_install_repo_enabled` | `true` | Render the source as enabled or disabled (`Enabled: no`) |
| `apt_install_repo_types` | `[deb]` | DEB822 types: `deb`, `deb-src` |
| `apt_install_repo_suites` | `[{{ ansible_facts['distribution_release'] }}]` | Suites; may be `*` or `any-version` for third-party repos |
| `apt_install_repo_components` | `[main]` | Components; may be `*` |
| `apt_install_pinning` | `true` | Write `/etc/apt/preferences.d/90<repo>` |
| `apt_install_pinning_package` | `*` | Pin `Package:` glob |
| `apt_install_pinning_pin_release` | empty | `Pin: release ...` when set, otherwise `Pin: origin <first apt_install_repo_uris hostname>` |
| `apt_install_pinning_pin_priority` | `900` | Pin priority |
| `apt_install_unattended_upgrade` | `true` | Write `/etc/apt/apt.conf.d/90unattended-upgrades-<repo>` |
| `apt_install_unattended_upgrade_origins_pattern` | empty | Explicit origins pattern; defaults to `site=<hostname>` |
| `apt_install_repo_packages` | `[]` | Packages installed from the new repository |
| `apt_install_mark_hold` | `false` | `apt-mark hold` every package in `apt_install_repo_packages` |

`apt_install_pinning: false` and `apt_install_unattended_upgrade: false` are revert switches: the
role removes a leftover file instead of writing one.

## Notes

- The role removes a legacy `/etc/apt/sources.list.d/<apt_install_repo>.list` before
  rendering the DEB822 source.
- `apt_install_dpkg_architectures` maps `ansible_facts['architecture']` to the dpkg
  architecture name used in the source file; unknown architectures are passed
  through unchanged.
