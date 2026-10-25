# debian_base

Applies a Debian baseline to freshly provisioned hosts: curated packages, DEB822
archive and security sources, unattended-upgrades wiring, and common bootstrap
settings.

Targets Debian 12/13 only (`ansible_facts['distribution'] == 'debian'`).

## What It Does

- Renders `/etc/apt/sources.list.d/debian.sources` and `debian-security.sources`
  in DEB822 format and replaces `/etc/apt/sources.list` with a placeholder.
- Installs `python3-debian` (needed by `ansible.builtin.deb822_repository`),
  runs an `apt upgrade`, and installs the baseline package list.
- Manages unattended-upgrades for stable updates and, optionally, backports and
  automatic reboots.
- Forcibly uses IPv4 for APT when enabled, and optionally adds a
  `debian-backports` pinning file.
- Grants the `sudo` group passwordless sudo via `community.general.sudoers`.
- Optionally enables TCP BBR (`community.general.modprobe` + `ansible.posix.sysctl`),
  `net.ipv4.ip_forward`, custom `sshd_config` entries, custom sysctl entries,
  and the `qemu-guest-agent` service.  All role-managed sysctls go to
  `/etc/sysctl.d/90-ansible-debian-base.conf`, never to `/etc/sysctl.conf`.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `debian_base_apt_repo_debian_uris` | `[https://deb.debian.org/debian/]` | Debian archive mirrors |
| `debian_base_apt_repo_debian_suites` | release + `-updates` | Archive suites |
| `debian_base_apt_repo_debian_components` | main/contrib/non-free/non-free-firmware | Archive components |
| `debian_base_apt_repo_debian_security_uris` | `[https://deb.debian.org/debian-security/]` | Security mirrors |
| `debian_base_apt_repo_debian_security_suites` | release + `-security` | Security suites |
| `debian_base_apt_repo_debian_backports_enabled` | `false` | Add the backports suite and pinning file |
| `debian_base_apt_repo_debian_backports_preferences_package` | `linux-* initramfs-tools` | Backports pinning `Package:` glob |
| `debian_base_apt_repo_debian_backports_preferences_pin_priority` | `500` | Backports pin priority |
| `debian_base_unattended_upgrade_updates_enabled` | `false` | Unattended-upgrades for `<release>-updates` |
| `debian_base_unattended_upgrade_backports_enabled` | `false` | Unattended-upgrades for backports |
| `debian_base_unattended_upgrade_automatic_reboot_enabled` | `false` | Unattended-upgrades automatic reboot |
| `debian_base_unattended_upgrade_automatic_reboot_time` | `02:00` | Automatic reboot time |
| `debian_base_apt_force_ipv4_enabled` | `true` | Write `/etc/apt/apt.conf.d/99force-ipv4` |
| `debian_base_tcp_bbr_enabled` | `false` | Load `tcp_bbr` and write the BBR sysctls to the role drop-in |
| `debian_base_ip_forward_enabled` | `false` | Set `net.ipv4.ip_forward=1` in the role drop-in |
| `debian_base_qemu_guest_agent_enabled` | `true` | Install and enable `qemu-guest-agent` |
| `debian_base_custom_sshd_config_enabled` | `false` | Apply `debian_base_custom_sshd_config_entries` |
| `debian_base_custom_sysctl_conf_enabled` | `false` | Apply `debian_base_custom_sysctl_conf_entries` to the role drop-in |
| `debian_base_apt_packages` | curated list | Packages installed as the baseline |

## Notes

- The `qemu-guest-agent` task notifies a handler that enables the service; on
  hardware without the virtio device the package still installs, but the service
  stays inactive.
- The first run reports changes because it runs `apt upgrade`. The upgrade task
  refreshes the APT index after the DEB822 sources and the backports suite are
  written, so packages from a newly enabled suite are upgraded in the same run.
  Repeat runs report no change once the system is up to date.
- Sysctls managed by this role live in
  `/etc/sysctl.d/90-ansible-debian-base.conf`.  Host-specific `99-*` drop-ins
  load later and intentionally take precedence; remove an old hand-managed
  file such as `99-bbr-network.conf` if the role should be authoritative.
- `debian_base_custom_sysctl_conf_entries` is a disabled-by-default set of
  optional examples, not a universal tuning recommendation.  The entries
  document their trade-offs; benchmark the target workload before enabling
  them.  TCP buffer and dirty-page settings are deliberately left to the
  RAM- and workload-dependent kernel defaults, with commented examples.
