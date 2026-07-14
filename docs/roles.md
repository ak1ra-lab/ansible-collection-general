# Roles

## acme_dns

Deploys an acme-dns server: a limited DNS server with a RESTful HTTP API for
handling ACME DNS-01 challenges.

Primary inputs:

- `acme_dns_domain`
- `acme_dns_server_ip`
- `acme_dns_nsadmin`
- `acme_dns_api_tls`
- `acme_dns_listen`
- `acme_dns_api_ip`
- `acme_dns_api_port`
- `acme_dns_api_corsorigins`

Primary outcomes:

- acme-dns Go binary built on localhost via `go_build` and deployed to the target
- systemd service running the acme-dns DNS server
- config file templated with domain, NS records, API TLS settings, and log configuration

After deployment, you must add delegation records at your upstream DNS
provider so that the acme-dns domain is delegated to the acme-dns server.

The number of A records depends on whether `acme_dns_nsname` differs from
`acme_dns_domain`.

**When `acme_dns_nsname != acme_dns_domain`** (separate nameserver name),
three records are needed:

> Example with `acme_dns_server_ip: xx.xx.xx.xx`,
> `acme_dns_domain: auth.acme-dns.example.com`,
> `acme_dns_nsname: ns1.acme-dns.example.com`:

| Type | Name                                  | Value                      | Purpose                        |
|------|---------------------------------------|----------------------------|--------------------------------|
| A    | `auth.acme-dns.example.com`           | `xx.xx.xx.xx`              | zone apex reachable            |
| NS   | `auth.acme-dns.example.com`           | `ns1.acme-dns.example.com` | delegate the zone              |
| A    | `ns1.acme-dns.example.com`            | `xx.xx.xx.xx`              | glue for the nameserver        |

**When `acme_dns_nsname == acme_dns_domain`** (default), the NS delegates to
itself and a single A record serves as both glue and zone apex:

> Example with `acme_dns_server_ip: xx.xx.xx.xx`,
> `acme_dns_domain: auth.acme-dns.example.com`,
> `acme_dns_nsname: auth.acme-dns.example.com` (default):

| Type | Name                                  | Value         | Purpose                       |
|------|---------------------------------------|---------------|-------------------------------|
| A    | `auth.acme-dns.example.com`           | `xx.xx.xx.xx` | both glue and zone apex       |
| NS   | `auth.acme-dns.example.com`           | `auth.acme-dns.example.com` | delegate the zone    |

Without these records, DNS-01 challenge lookups for `*.auth.acme-dns.example.com`
will not reach the acme-dns instance.

## acme_dns_register

Registers a client with an acme-dns server, persists the resulting credentials
to a host_vars directory, and optionally creates `_acme-challenge` CNAME records.

Primary inputs:

- `acme_dns_register_server_url`
- `acme_dns_register_username`
- `acme_dns_register_password`
- `acme_dns_register_subdomain`
- `acme_dns_register_acme_domains`
- `acme_dns_register_cloudflare_api_token`
- `acme_dns_register_cloudflare_zone_token`

Primary outcomes:

- acme-dns account registered via POST /register
- credentials persisted to `acme_dns_credentials.yaml` in the configured directory
- `_acme-challenge` CNAME records added via Cloudflare API or prompted for manual creation

## debian_base

Applies a Debian or Ubuntu baseline for freshly provisioned hosts.

Primary inputs:

- `debian_base_apt_repo_debian_uris`
- `debian_base_apt_repo_debian_security_uris`
- `debian_base_apt_repo_debian_backports_enabled`
- `debian_base_unattended_upgrade_updates_enabled`
- `debian_base_unattended_upgrade_automatic_reboot_enabled`
- `debian_base_apt_force_ipv4_enabled`
- `debian_base_tcp_bbr_enabled`
- `debian_base_custom_sshd_config_enabled`
- `debian_base_custom_sysctl_conf_enabled`
- `debian_base_apt_packages`

Primary outcomes:

- Debian archive and security repositories rendered in DEB822 format
- unattended-upgrades toggled for stable updates and optional backports
- baseline packages installed for day-to-day host administration
- optional TCP BBR, SSH hardening entries, sysctl tuning, and qemu-guest-agent enablement

## go_build

Builds a Go project from a Git repository on `localhost` and caches a metadata
stamp so repeated runs rebuild only when inputs change.

Primary inputs:

- `go_build_repo_url`
- `go_build_output_name`
- `go_build_repo_version`
- `go_build_package`
- `go_build_static`
- `go_build_goos`
- `go_build_goarch`

Primary outputs:

- `go_build_repo_dir`
- `go_build_binary_path`
- `go_build_stamp_path`

## pyproject_install

Installs a Python package into a virtual environment on the target host.

Supported sources:

- `local`: build a wheel with `uv build --wheel` on `localhost`, copy it to the remote host, and install it with `pip`.
- `pypi`: install from the public PyPI index.
- `testpypi`: install from TestPyPI with PyPI as an extra index.

Primary inputs:

- `pyproject_install_source`
- `pyproject_install_package_name`
- `pyproject_install_package_extras`
- `pyproject_install_local_project_root`
- `pyproject_install_venv_dir`
- `pyproject_install_remote_tmp_dir`
- `pyproject_install_system_packages`
