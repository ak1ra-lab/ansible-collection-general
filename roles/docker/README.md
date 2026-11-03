# docker

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Installs Docker CE from the official Docker APT repository (through
`ak1ra_lab.general.apt_repository`), installs and optionally holds the Docker
packages, templates `/etc/docker/daemon.json`, adds regular users to the
`docker` group, and starts and enables `docker.service`.

Targets Debian 12/13 and Ubuntu 22.04 and later. The Docker repository path
(`https://download.docker.com/linux/<distribution>`) is derived from
`docker_apt_repo_distribution`.

## Variables

The canonical variable reference is generated from `meta/argument_specs.yml` in
the collection documentation.

## daemon.json

The role assembles `/etc/docker/daemon.json` from role defaults,
`docker_daemon_options`, and the dedicated mirror and proxy variables. The
defaults are:

- `exec-opts: ["native.cgroupdriver=systemd"]`
- `log-driver: json-file` with `max-size: 100m` and `max-file: 3`
- `registry-mirrors` from `docker_daemon_registry_mirrors`

The role does not force a storage driver; Docker selects the default for the
host filesystem. Set `docker_daemon_options.storage-driver` when an explicit
driver is required.

`docker_daemon_options` is merged recursively over the defaults, so callers can
override one log option or add settings such as `data-root` without repeating
the rest of the file:

```yaml
docker_daemon_options:
  data-root: /srv/docker
  log-opts:
    max-size: 50m
    max-file: "5"
  default-address-pools:
    - base: 172.31.0.0/16
      size: 24
```

When `docker_daemon_proxies` is non-empty, the file also contains a `proxies`
object with `http-proxy`, `https-proxy`, and `no-proxy`, which applies to the
daemon's registry and swarm traffic. Changes notify a restart of
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
