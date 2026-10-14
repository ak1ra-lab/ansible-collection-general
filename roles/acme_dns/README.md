# acme_dns

Deploys an [acme-dns](https://github.com/acme-dns/acme-dns) server: a limited DNS
server with a RESTful HTTP API for handling ACME DNS-01 challenges.

## How It Works

1. `ak1ra_lab.general.go_build` clones and builds the acme-dns binary on
   `localhost` (the Ansible controller).
2. A dedicated system user, group, and directories are created on the target.
3. The binary, the rendered `config.cfg`, and the systemd unit are deployed.
4. `acme-dns.service` is started and enabled.

## Required Variables

- `acme_dns_domain` - domain served by this instance, e.g. `auth.acme-dns.example.com`
- `acme_dns_server_ip` - public IP used in the rendered A records
- `acme_dns_nsadmin` - admin email with `@` replaced by `.`
- `acme_dns_api_tls` - `none`, `letsencrypt`, or `letsencryptstaging`

## Common Variables

| Variable | Default | Description |
| --- | --- | --- |
| `acme_dns_nsname` | `{{ acme_dns_domain }}` | Nameserver hostname used in the NS delegation |
| `acme_dns_listen` | `0.0.0.0:53` | DNS listen address |
| `acme_dns_protocol` | `both` | DNS protocol (`both4`, `udp6`, ...) |
| `acme_dns_api_ip` | `0.0.0.0` | API listen IP |
| `acme_dns_api_port` | `6443` | API listen port |
| `acme_dns_api_corsorigins` | `[]` | API CORS allowed origins |
| `acme_dns_db_engine` | `sqlite3` | `sqlite3` or `postgres` |
| `acme_dns_db_connection` | `acme-dns.db` | Database connection string |
| `acme_dns_loglevel` / `acme_dns_logformat` | `info` / `json` | Log configuration |
| `acme_dns_user` / `acme_dns_group` | `acme-dns` | System user and group |
| `acme_dns_home_dir` / `acme_dns_config_dir` | `/var/lib/acme-dns` / `/etc/acme-dns` | Data and config directories |
| `acme_dns_install_dir` | `/usr/local/bin` | Binary install directory |
| `acme_dns_go_build_*` | see defaults | Overrides passed to `go_build` |

## DNS Delegation

Upstream delegation records must be added after deployment; the required A/NS
records for both the separate-nameserver and self-delegating layouts are
documented in [`docs/roles.md`](../../docs/roles.md#acme_dns).

## Requirements

- `go` must be available on the controller (`go_build` fails immediately if not).
- The target must be able to bind the configured DNS and API addresses; when TLS
  is handled by a reverse proxy, use `acme_dns_api_tls: none`.
