# docker

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Installs Docker CE from the official Docker APT repository (through
`ak1ra_lab.general.apt_repository`), installs and optionally holds the Docker
packages, templates `/etc/docker/daemon.json`, adds regular users to the
`docker` group, and starts and enables `docker.service`.

Targets Debian 12/13 only, matching the Debian repository
(`https://download.docker.com/linux/debian`).

## Variables

The canonical variable reference is generated from `meta/argument_specs.yml` in
the collection documentation.

## daemon.json

The template always writes:

- `exec-opts: ["native.cgroupdriver=systemd"]`
- `log-driver: json-file` with `max-size: 100m`
- `storage-driver: overlay2`
- `registry-mirrors` from `docker_daemon_registry_mirrors`

When `docker_daemon_proxies` is non-empty, it also writes a `proxies` object
with `http-proxy`, `https-proxy`, and `no-proxy`. This configures the Docker
daemon's own registry and swarm traffic and is separate from the APT proxy and
from Ansible module downloads. Newer Docker Engine releases support this key;
Docker Desktop ignores it.

The file is written with `force: true` and notifies a restart of
`docker.service`.

## Keyring download

Use `docker_apt_keyrings_proxy` and `docker_apt_keyrings_no_proxy` when the
keyring download needs a proxy. `docker_apt_keyrings_checksum` and
`docker_apt_keyrings_force` control integrity checks and refreshes.

## Notes

- The role imports `ak1ra_lab.general.apt_repository` internally; do not apply
  `apt_repository` for the Docker repository yourself.
- The package installation and hold steps live in this role because
  `apt_repository` never installs packages from the repository it configures.
- Regular users are detected by parsing `/etc/passwd` for `uid >= 1000` with a
  login shell; if no such user exists, the group step is a no-op.
