# acme_dns_register

Registers one [acme-dns](https://github.com/joohoi/acme-dns) account per
**validation domain**, persists the resulting domain -> account mapping to a
host_vars directory, and creates the required `_acme-challenge` CNAME records.

Registration runs on the managed host (it needs access to the acme-dns API).
The host_vars registry write and the Cloudflare/manual CNAME tasks are
delegated to the Ansible controller (`delegate_to: localhost`).

A validation domain is the ACME identifier with any leading `*.` removed:

- `example.com` and `*.example.com` share one account and one
  `_acme-challenge.example.com` CNAME.
- `www.example.com` gets its own account and its own
  `_acme-challenge.www.example.com` CNAME.

Each acme-dns account can hold two TXT values (one for a base domain and one
for its wildcard). That is a limit of the acme-dns server, not of ACME; a
certificate can contain many validation domains as long as each one has an
account.

## Behavior

1. Normalizes `acme_dns_register_acme_domains` by stripping leading `*.` and
   deduplicating the result.
2. Reuses accounts from `acme_dns_register_accounts`; registers missing
   domains with `POST /register`.
3. Persists the complete registry to
   `<credentials_dir>/acme_dns_credentials.yaml` (mode `0600`):

   ```yaml
   acme_dns_register_server_url: https://auth.example.com
   acme_dns_register_accounts:
     example.com:
       username: ...
       password: ...
       subdomain: ...
       fulldomain: ...
     www.example.com:
       username: ...
       password: ...
       subdomain: ...
       fulldomain: ...
   ```

4. When a Cloudflare token is available, reconciles one CNAME per validation
   domain, pointing at that domain's own fulldomain.
5. Without a Cloudflare token, displays the required CNAME records after a
   fresh registration and optionally waits for the operator
   (`acme_dns_register_manual_prompt: false` disables the prompt).

Wildcard identifiers use the same `_acme-challenge.<base>` record as the base
domain; the two values coexist in the same account's two TXT slots.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `acme_dns_register_server_url` | empty | **(required when registering)** acme-dns server URL |
| `acme_dns_register_accounts` | `{}` | Existing domain -> account mapping |
| `acme_dns_register_acme_domains` | `[]` | ACME identifiers needing accounts/CNAMEs |
| `acme_dns_register_cloudflare_api_token` | empty | Cloudflare account token |
| `acme_dns_register_cloudflare_zone_token` | empty | Zone-scoped token (preferred) |
| `acme_dns_register_cloudflare_zone` | empty | Global Cloudflare zone fallback |
| `acme_dns_register_cloudflare_zones` | `{}` | Per-validation-domain Cloudflare zone overrides |
| `acme_dns_register_manual_prompt` | `true` | Pause for manual CNAME creation after a fresh registration |
| `acme_dns_register_credentials_dir` | `{{ playbook_dir }}/host_vars/{{ inventory_hostname }}` | Account registry output directory |

The Cloudflare zone for a domain is selected in this order:

1. `acme_dns_register_cloudflare_zones[<validation domain>]`
2. `acme_dns_register_cloudflare_zone`
3. The last two labels of the validation domain

Set the mapping explicitly for public suffixes such as `example.co.uk`, or for
domains that span several zones.

## Facts

After the role runs the play has:

- `acme_dns_register_accounts` - the effective domain -> account mapping
- `acme_dns_register_new_domains` - domains registered during this run
- `acme_dns_register_newly_registered` - true when the list is non-empty

## Notes

- Registration happens once per validation domain; re-runs with the persisted
  registry skip existing accounts. Load the file (for example with
  `vars_files:`) or let `ak1ra_lab.general.certbot` load it automatically when
  `certbot_dns_provider: acmedns`.
- With a Cloudflare token, CNAME records are reconciled on every run, so
  adding a validation domain later only requires re-running the role.
- Without a Cloudflare token, the manual prompt is unsuitable for
  non-interactive runs; create the CNAMEs by another mechanism and set
  `acme_dns_register_manual_prompt: false`.
- Credential handling is marked `no_log`; keep `-v` runs out of shared logs.
