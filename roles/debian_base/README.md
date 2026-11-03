# debian_base

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

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
- Configures an optional APT HTTP/HTTPS proxy, forcibly uses IPv4 for APT when
  enabled, and optionally adds a `debian-backports` pinning file.
- Grants the `sudo` group passwordless sudo via `community.general.sudoers`.
- Optionally enables TCP BBR (`community.general.modprobe` + `ansible.posix.sysctl`),
  `net.ipv4.ip_forward`, a role-owned sshd drop-in, custom sysctl entries,
  and the `qemu-guest-agent` service.  All role-managed sysctls go to
  `/etc/sysctl.d/90-ansible-debian-base.conf`, never to `/etc/sysctl.conf`.

## Variables

The canonical variable reference is generated from `meta/argument_specs.yml` in
the collection documentation.

The long default lists (`debian_base_apt_packages` and the sshd/sysctl entry
lists) are stored as internal `_debian_base_*` values in `vars/main.yml`. The
public variables stay in `defaults/main.yml`, so play vars, inventory vars, role
params, and `-e @file.yml` overrides keep their normal precedence.

## APT proxy

`debian_base_apt_http_proxy` and `debian_base_apt_https_proxy` render the
role-owned `/etc/apt/apt.conf.d/90ansible-debian-base-proxy` drop-in through
`apt_conf`. Both settings are applied before the first APT network operation.
An empty value removes the corresponding option; when both are empty the file
is removed.

## Notes

- `qemu-guest-agent` is managed only on QEMU/KVM guests. On bare metal,
  containers, and other hypervisors the role removes the package. Other
  hypervisor guest agents are not managed by this role.
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
- The custom sshd entries disable both `PasswordAuthentication` and
  `KbdInteractiveAuthentication` (PAM keyboard-interactive can otherwise still
  prompt for a password).  They are rendered into the role-owned
  `/etc/ssh/sshd_config.d/00-ansible-debian-base.conf`, validated with
  `sshd -t`, and notify a reload of `ssh.service`.  The `00-` prefix makes it
  the first drop-in; OpenSSH keeps the first obtained value.  Directives
  already present in `/etc/ssh/sshd_config` before its `Include` line still win
  and must be reconciled manually; verify the effective values with `sshd -T`.
  Entries are plain sshd_config lines rendered in order; they no longer use
  `regexp`/`lineinfile`.  Lines written into `/etc/ssh/sshd_config` by earlier
  versions of this role are not removed automatically.
- The package list intentionally uses `bind9-dnsutils`, `7zip` and `gnupg`
  instead of the removed/transitional `dnsutils`, `p7zip`/`p7zip-full` and
  `gnupg2` names.  `systemd-cron` conflicts with `cron`/`anacron`, so hosts
  that already run a classic cron daemon will have it replaced.
