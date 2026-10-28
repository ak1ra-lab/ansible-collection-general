# Getting started

## Install the collection

The collection is currently consumed from Git; it is not published to Galaxy.
Create a `requirements.yaml` in the consuming repository:

```yaml
---
collections:
  - name: git+https://github.com/ak1ra-lab/ansible-collection-general.git
    version: master
```

Install it into the project-local collections path:

```shell
ansible-galaxy collection install -r requirements.yaml -p ./.ansible/collections
```

The consuming repository's `ansible.cfg` should put that path at the front of
`collections_path`. Pin a tag or commit instead of `master` for reproducible
deployments.

## Control-node requirements

- `ansible-core >= 2.18` (`meta/runtime.yml`).
- The collection dependencies are installed automatically by
  `ansible-galaxy`: `ansible.posix`, `community.general`, and
  `kubernetes.core`.
- The Kubernetes Python client is required for `cert_manager`:

  ```shell
  uv add kubernetes
  # or: python -m pip install kubernetes
  ```

- `go` is required on the controller for `go_build`, which builds binaries on
  `localhost`.
- `uv` is required on the controller for `pyproject_install` when
  `pyproject_install_source: local` builds a wheel from a local project.

## Managed-node requirements

The APT-based roles target Debian 12 and Debian 13. The Molecule scenarios use
the systemd-enabled `debian:12` and `debian:13` container images from
[ak1ra-lab/docker-systemd](https://github.com/ak1ra-lab/docker-systemd).

Role-specific requirements:

| Role | Requirements |
| --- | --- |
| `acme_dns` | A delegated DNS zone and a target reachable on the DNS and API ports. The Go binary is built on the controller through `go_build`. |
| `acme_dns_register` | Network access to the acme-dns API; a Cloudflare API token for automatic CNAME creation, or manual CNAME creation. |
| `apt_install` | Debian; root privileges for the keyring and APT source files. |
| `cert_manager` | A kubeconfig with permission to manage cluster-scoped cert-manager resources; the role delegates to `cert_manager_delegate_to` (default `localhost`). |
| `certbot` | systemd host; DNS API credentials for DNS-01, or a reachable HTTP-01 endpoint. |
| `debian_base` | Debian; root privileges. |
| `docker` | Debian; root privileges. The role imports `apt_install` for the Docker repository. |
| `go_build` | `go` on the controller; the build runs on `localhost`, not the managed host. |
| `pyproject_install` | A target Python environment; `uv` on the controller for local wheel builds. |

See each role README for the full variable contract and deployed artifacts.

## First playbooks

The bundled entry points accept `playbook_hosts`; each playbook's `hosts`
expression documents its default inventory group.

```shell
ansible-playbook playbooks/acme-dns.yaml -e playbook_hosts=acme-dns
ansible-playbook playbooks/certbot.yaml -e playbook_hosts=certbot
ansible-playbook playbooks/debian-base-defaults.yaml -e playbook_hosts=web
ansible-playbook playbooks/docker-vps.yaml -e playbook_hosts=web
```

The example playbooks under `playbooks/apt_install/` and
`playbooks/go_build/` are runnable recipes for specific packages and build
targets. See [Playbooks](playbooks.md) for the layout and examples.

## Next steps

- [Roles](roles/index.md) for the per-role variable contracts.
- [Modules](modules.md) for `github_releases_info` and `cpu_info`.
- [Architecture](architecture.md) for how the role families compose.
