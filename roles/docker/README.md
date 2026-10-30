# docker

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Installs Docker CE from the official Docker APT repository (through
`ak1ra_lab.general.apt_install`), templates `/etc/docker/daemon.json`, adds
regular users to the `docker` group, and starts and enables `docker.service`.

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

The file is written with `force: true` and notifies a restart of
`docker.service`.

## Notes

- The role imports `ak1ra_lab.general.apt_install` internally; do not apply
  `apt_install` for the Docker repository yourself.
- Regular users are detected by parsing `/etc/passwd` for `uid >= 1000` with a
  login shell; if no such user exists, the group step is a no-op.
