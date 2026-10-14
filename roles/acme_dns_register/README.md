# acme_dns_register

Registers a client (one subdomain) with an acme-dns server, persists the
resulting credentials to a host_vars directory, and creates the required
`_acme-challenge` CNAME records.

All tasks run on the Ansible controller (`delegate_to: localhost`).

## Behavior

1. Validates `acme_dns_register_server_url` and any pre-configured credentials.
2. `POST /register` when no complete credential set was supplied; the response
   is written to `<credentials_dir>/acme_dns_credentials.yaml` (mode `0600`).
3. When newly registered and a Cloudflare token is available,
   `_acme-challenge` CNAME records are created through the Cloudflare API.
4. Otherwise the role prints the records and waits for the operator to add them
   before continuing.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `acme_dns_register_server_url` | empty | **(required)** acme-dns server URL |
| `acme_dns_register_username` / `_password` / `_subdomain` | empty | Existing credentials; all three skip registration |
| `acme_dns_register_cloudflare_api_token` | empty | Cloudflare account token |
| `acme_dns_register_cloudflare_zone_token` | empty | Zone-scoped token (preferred) |
| `acme_dns_register_cloudflare_zone` | empty | Explicit zone; derived from the hostname when empty |
| `acme_dns_register_hostname` | `{{ inventory_hostname }}` | Host FQDN used to derive the Cloudflare zone |
| `acme_dns_register_acme_domains` | `[]` | Domains needing `_acme-challenge` CNAMEs |
| `acme_dns_register_credentials_dir` | `{{ playbook_dir }}/host_vars/{{ inventory_hostname }}` | Credential output directory |

## Facts

After the role runs the play has:

- `acme_dns_register_newly_registered` - true when a fresh registration happened
- `acme_dns_register_username` / `_password` / `_subdomain` - the effective credentials
- `acme_dns_register_fulldomain` - the server-reported `fulldomain`

## Notes

- Registration happens once per subdomain; re-runs with the persisted
  credentials skip it.
- The manual path uses `ansible.builtin.pause`, so it is unsuitable for
  non-interactive runs without a Cloudflare token.
- Credential handling is marked `no_log`; keep `-v` runs out of shared logs.
