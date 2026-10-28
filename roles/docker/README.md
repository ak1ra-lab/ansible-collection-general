# docker

Installs Docker CE from the official Docker APT repository (through
`ak1ra_lab.general.apt_install`), templates `/etc/docker/daemon.json`, adds
regular users to the `docker` group, and starts and enables `docker.service`.

Targets Debian 12/13 only, matching the Debian repository
(`https://download.docker.com/linux/debian`).

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `docker_apt_keyrings_url` | Docker Debian GPG key | Keyring URL passed to `apt_install` |
| `docker_apt_keyrings_dest` | `/etc/apt/keyrings/docker-ce.asc` | Keyring destination |
| `docker_apt_repo` | `docker-ce` | DEB822 repository name and legacy `.list` name |
| `docker_apt_repo_uris` | `[https://download.docker.com/linux/debian]` | Repository mirrors |
| `docker_apt_repo_suites` | `{{ ansible_facts['distribution_release'] }}` | Repository suite |
| `docker_apt_repo_components` | `stable` | Repository component |
| `docker_apt_pinning` | `true` | Pin the Docker packages (priority 900, origin Docker) |
| `docker_apt_pinning_package` | `docker-* containerd.io` | Packages covered by the pinning file |
| `docker_apt_pinning_pin_release` | `o=Docker,a=<suite>,c=<component>` | `Pin: release` line; empty falls back to the repository hostname |
| `docker_apt_unattended_upgrade` | `false` | Allow unattended Docker upgrades |
| `docker_apt_unattended_upgrade_origins_pattern` | `origin=Docker,suite=<suite>,component=<component>` | Origins pattern passed to `apt_install` |
| `docker_apt_mark_hold` | `false` | `apt-mark hold` the Docker packages |
| `docker_apt_repo_packages` | docker-ce, docker-ce-cli, containerd.io, buildx, compose, skopeo | Packages installed from the repository |
| `docker_daemon_registry_mirrors` | `[]` | `registry-mirrors` written to `daemon.json` |

## daemon.json

The template always writes:

- `exec-opts: ["native.cgroupdriver=systemd"]`
- `log-driver: json-file` with `max-size: 100m`
- `storage-driver: overlay2`
- `registry-mirrors` from `docker_daemon_registry_mirrors`

The file is written with `force: true` and notifies a restart of
`docker.service`.

## Notes

- The role imports `ak1ra_lab.general.apt_install` internally; do not apply
  `apt_install` for the Docker repository yourself.
- Regular users are detected by parsing `/etc/passwd` for `uid >= 1000` with a
  login shell; if no such user exists, the group step is a no-op.
