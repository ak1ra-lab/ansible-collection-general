# acme_dns_register

Registers a client (one subdomain) with an acme-dns server, persists the
resulting credentials to a host_vars directory, and creates the required
`_acme-challenge` CNAME records.

All tasks run on the Ansible controller (`delegate_to: localhost`).

## Behavior

1. Validates `acme_dns_register_server_url` and any pre-configured credentials.
2. `POST /register` when no complete credential set was supplied; the response
   is written to `<credentials_dir>/acme_dns_credentials.yaml` (mode `0600`).
   The file now includes `acme_dns_register_fulldomain`, so later runs can
   reconcile the CNAME records without registering again.  Older files without
   it derive the value from the server URL.
3. When the fulldomain is known and a Cloudflare token is available,
   `_acme-challenge` CNAME records are ensured on every run
   (`community.general.cloudflare_dns` is idempotent); wildcard domains use
   the same `_acme-challenge.<base>` name as the base domain.
4. After a fresh registration without a Cloudflare token, the role prints the
   records and waits for the operator to add them before continuing.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `acme_dns_register_server_url` | empty | **(required)** acme-dns server URL |
| `acme_dns_register_username` / `_password` / `_subdomain` | empty | Existing credentials; all three skip registration |
| `acme_dns_register_fulldomain` | empty | Existing CNAME target; derived from the server URL when empty |
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
  credentials skip it.  Load the persisted file (for example with
  `vars_files: - host_vars/{{ inventory_hostname }}/acme_dns_credentials.yaml`)
  or let `ak1ra_lab.general.certbot` load it automatically when
  `certbot_dns_provider: acmedns`.
- With a Cloudflare token, the CNAME records are reconciled on every run, so
  adding a domain later does not require a new registration.  Without a token,
  the manual prompt only runs after a fresh registration.
- Wildcard domains (`*.example.com`) and their base domain share the same
  `_acme-challenge.example.com` CNAME.
- acme-dns stores a small rolling set of TXT values per account (the upstream
  server keeps two); therefore a single certificate should contain at most two
  names, typically `example.com` and `*.example.com`.
- Without a Cloudflare token, the manual path uses `ansible.builtin.pause`, so
  it is unsuitable for non-interactive runs.
- Credential handling is marked `no_log`; keep `-v` runs out of shared logs.
