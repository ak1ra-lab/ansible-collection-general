# certbot

Obtain and renew TLS certificates with [certbot](https://certbot.eff.org/) on a
systemd host. DNS-01 is the primary challenge type; HTTP-01 is available for
hosts without DNS API access.

The role only obtains certificates. Services that consume them (nginx, ...) are
configured by their own roles and can reload after a renewal through the global
`certbot_deploy_hooks` or a certificate's own `deploy_hooks`.

## Installation Sources

| Source | Behavior |
| --- | --- |
| `apt` (default) | Installs `certbot` and `python3-certbot-dns-<provider>` from the distribution. Security updates come from apt; Debian 12 ships certbot 2.1 and Debian 13 ships 4.0. |
| `pypi` | Installs `certbot` and `certbot-dns-<provider>` into an isolated virtualenv through `ak1ra_lab.general.pyproject_install` (`/var/lib/certbot/venv` by default). Useful for a newer certbot than the distribution provides. |
| `none` | Uses an externally provided certbot (snap, image, ...); set `certbot_bin`. The role does not manage the units or timer in this mode. |

The role never mixes the two binaries: the systemd unit, the issuance command
and the renewal timer all use `certbot_bin` (the distribution path, the venv
path, or the explicit path). A leftover `/usr/bin/certbot` is reported as a
warning when `pypi` is selected.

The distribution package already ships the systemd units, `cli.ini` and
logrotate configuration. The role only renders its own copies for `pypi`
installs, when the certbot directories are relocated, or when the
corresponding `certbot_manage_*` flag is enabled explicitly.

## Certificates

`certbot_certificates` is a list; each entry supports:

| Key | Required | Description |
| --- | --- | --- |
| `name` | no | Lineage name (`--cert-name`). Defaults to the first domain with a leading `*.` stripped, matching certbot. |
| `domains` | yes | List of DNS names, e.g. `[example.com, "*.example.com"]`. |
| `force` | no | Re-issue even when the lineage already matches (default `false`). |
| `deploy_hooks` | no | Shell commands run only when this lineage renews. See [Renewal](#renewal). |
| `extra_args` | no | Extra certbot arguments for this certificate. |

On every run the role compares the SANs of an existing lineage with the
requested domains. A missing lineage, a changed domain set, or `force: true`
triggers `certbot certonly --cert-name ...`; an unchanged lineage is left
alone, so repeat runs do not consume ACME rate limits. Changing the domain set
re-issues the lineage in place (`--cert-name` semantics), including adding new
SANs. This is intentional: `--cert-name` with the complete domain list is
certbot's recommended replacement for `--expand`, because it can also remove
domains, whereas `--expand` can only add them. The role therefore does not pass
`--expand`.

```yaml
certbot_email: admin@example.com
certbot_certificates:
  - name: example.com
    domains:
      - example.com
      - "*.example.com"
```

`certbot_key_type` defaults to `ecdsa` (certbot's own default since 2.0). Set
it to `rsa` to use `certbot_rsa_key_size` (4096) instead.

## External account binding (EAB)

Some ACME CAs require external account binding; ZeroSSL is the most common
example, and Google Trust Services and SSL.com also use it. EAB is part of
certbot's ACME client, not a plugin, so no extra package is needed:

```yaml
certbot_acme_server: https://acme.zerossl.com/v2/DV90
certbot_eab:
  key_id: "..."
  hmac_key: "{{ vault_eab_hmac }}"
```

`hmac_key` is the base64url-encoded key string shown by the CA (for ZeroSSL:
Developer → EAB Credentials for ACME Clients); pass it verbatim (certbot
decodes it). HS256 requires a key of at least 32 bytes
(RFC 7518); CA-provided keys satisfy this. EAB is only needed while registering
the ACME account, so the role passes `--eab-kid`/`--eab-hmac-key` to `certonly`
and not to `renew`. certbot does not store EAB in the renewal configuration;
renewals use the account key under `/etc/letsencrypt/accounts`. Back that
directory up, and re-run the role if the account has to be recreated.

`certbot_eab` requires `certbot_acme_server` and cannot be combined with
`certbot_staging` (the staging flag selects the Let's Encrypt staging CA).
Debian 12 ships certbot 2.1, which already supports EAB and defaults to
HS256, the algorithm used by ZeroSSL and cert-manager.

## DNS-01

`certbot_dns_provider` selects the `certbot-dns-<provider>` plugin
(`cloudflare` by default). The credentials are a plain mapping of plugin INI
keys, so any certbot DNS plugin works without a per-provider template:

```yaml
certbot_dns_credentials:
  dns_cloudflare_api_token: "{{ vault_cloudflare_api_token }}"
```

The mapping is rendered to
`/etc/letsencrypt/credentials/<provider>.ini` (mode `0600`); the directory is
mode `0700`. For plugins that read credentials from the environment or an
instance profile (for example `route53`), leave the mapping empty and the
`--dns-<provider>-credentials` argument is omitted.

`certbot_dns_propagation_seconds` (default `30`) is passed as
`--dns-<provider>-propagation-seconds`.

### Cloudflare

Use a scoped API token with `Zone:Read` and `DNS:Edit` for the zones being
validated. The examples use that token, not the legacy global API key.

### acme-dns

`certbot_dns_provider: acmedns` uses certbot's manual plugin with the bundled
auth hook. The role stores **one acme-dns account per validation domain** in a
JSON registry (`/etc/letsencrypt/credentials/acmedns.json` by default); the
hook reads `CERTBOT_DOMAIN`, strips a leading `*.`, selects that domain's
account, and calls `/update` with only the Python standard library.

The registry is a domain -> account mapping:

```json
{
  "server_url": "https://auth.example.com",
  "accounts": {
    "example.com": {
      "username": "...",
      "password": "...",
      "subdomain": "...",
      "fulldomain": "..."
    },
    "www.example.com": {
      "username": "...",
      "password": "...",
      "subdomain": "...",
      "fulldomain": "..."
    }
  }
}
```

`example.com` and `*.example.com` share the `example.com` account because both
use `_acme-challenge.example.com`; `www.example.com` gets its own account.
Each acme-dns account has two TXT slots, so the base + wildcard pair fits
exactly. There is no per-certificate name limit: a certificate can contain
many SANs as long as each validation domain has its own account.

The accounts can come from the persisted
`host_vars/<inventory_hostname>/acme_dns_credentials.yaml` written by
`ak1ra_lab.general.acme_dns_register`, from `certbot_acmedns_accounts` (the
same `domain -> account` mapping; explicit entries override the persisted
registry), or be registered automatically:

```yaml
certbot_dns_provider: acmedns
certbot_acmedns_register: true
certbot_acmedns_server_url: https://auth.example.com
certbot_acmedns_cloudflare_api_token: "{{ vault_cloudflare_api_token }}"
certbot_certificates:
  - domains:
      - example.com
      - "*.example.com"
      - www.example.com
```

With `certbot_acmedns_register: true`, the role registers one account per
validation domain (`example.com` and `www.example.com`) and creates the
corresponding CNAME records. `certbot_acmedns_cloudflare_zones` maps
validation domains to zones when the last-two-labels heuristic is wrong or the
domains span multiple zones:

```yaml
certbot_acmedns_cloudflare_zones:
  example.com: example.com
  www.example.com: example.com
```

Without a Cloudflare token, the role displays the required CNAME records and
pauses after a fresh registration; set `certbot_acmedns_manual_prompt: false`
for non-interactive runs where CNAMEs are managed elsewhere. The CNAME for each
validation domain points at that domain's own fulldomain:

```text
_acme-challenge.example.com.      CNAME  <example.com-account>.auth.example.com.
_acme-challenge.www.example.com.  CNAME  <www-account>.auth.example.com.
```

## HTTP-01

Set `certbot_challenge: http-01` when DNS-01 is not an option:

```yaml
certbot_challenge: http-01
certbot_http01_method: standalone   # or webroot
certbot_http01_port: 80
certbot_webroot_path: /var/www/html
```

`standalone` is certbot's built-in HTTP-01 authenticator (`--standalone`): it
starts a temporary web server and binds `certbot_http01_port` (80 by default)
itself, so no other process may listen on that port. It is intended for hosts
without a web server, or when the web server can be stopped for validation. It
is unrelated to the third-party `siilike/certbot-dns-standalone` plugin, which
is a DNS-01 authenticator that runs a local authoritative DNS server.

Public ACME CAs always send the HTTP-01 request to **port 80**, regardless of
`certbot_http01_port`. A non-80 local port is useful in two cases only: a
private/test ACME server that validates on another port (Pebble defaults to
5002, for example), or an external port 80 that is DNATed/forwarded to the
local port. With a public CA and no port forwarding, keep the default 80.

`webroot` is also an HTTP-01 authenticator, but certbot only writes the
challenge file to `<certbot_webroot_path>/.well-known/acme-challenge/`; an
already running web server must serve that path for every requested domain on
port 80 (or on a local port that external port 80 is forwarded to).
`certbot_http01_port` is not used by webroot.

The role checks that the webroot exists and is an absolute path, but it does
not modify the web server configuration. All names in `certbot_certificates`
must be served from the same webroot; use separate role invocations if their
document roots differ.

For both methods the DNS A/AAAA records for every requested name must already
point at this host before issuance. The role does not check DNS: split-horizon,
CDN/proxy and multi-address setups make a local lookup unreliable, so certbot
and the ACME server report the real validation result.

The `--nginx` and `--apache` plugins are different: they are
authenticator/installer combinations that temporarily rewrite the web server
configuration and serve the challenge through the running server. They are
convenient when the role also owns that web server, but this role deliberately
stays web-server-neutral and supports only `standalone` and `webroot`. HTTP-01
cannot issue wildcard certificates.

## Renewal

The role enables `certbot.timer` (twice daily with a randomized delay and
`Persistent=true`). The managed unit's command is equivalent to:

```shell
/var/lib/certbot/venv/bin/certbot -q renew --no-random-sleep-on-renew
```

### Hook scope and lineage

`certbot_deploy_hooks` is global: every command runs after **any** successful
renewal. Use it for shared consumers such as a web server that serves several
certificates:

```yaml
certbot_deploy_hooks:
  - nginx -t && systemctl reload nginx
```

For a service that consumes only one certificate, use the certificate's own
`deploy_hooks` instead:

```yaml
certbot_certificates:
  - name: app.example.com
    domains:
      - app.example.com
    deploy_hooks:
      - install -d -m 0750 -o root -g app /etc/app/tls
      - >-
        install -m 0640 -o root -g app
        /etc/letsencrypt/live/app.example.com/fullchain.pem
        /etc/app/tls/fullchain.pem
      - systemctl reload app
```

The role renders one dispatcher,
`/etc/letsencrypt/renewal-hooks/deploy/certbot-deploy-hooks.sh`, which runs the
global commands and then uses the `RENEWED_LINEAGE` environment variable to
run only the matching certificate's hooks. certbot executes every executable in
`renewal-hooks/deploy/` for every renewed lineage, so per-certificate
selectivity has to live inside the script; creating one script per cert-name
would not isolate anything.

`/etc/letsencrypt/renewal/<name>.conf` is certbot's per-lineage configuration
(the `[renewalparams]` file it reads during `renew`); it is not a hook
directory. `/etc/letsencrypt/renewal-hooks/{pre,deploy,post}/` is where
executable hooks live. The role only manages the deploy script and does not
write certbot's renewal configuration.

Renewal granularity is the lineage, not an individual SAN. If several services
share one certificate, they all get the same renewal event; give each service
its own certificate if they need independent reloads. Global hooks run before
per-certificate hooks, and the script runs every configured hook even when one
fails, then exits non-zero.

### Non-root consumers

certbot creates `/etc/letsencrypt/live` and `/etc/letsencrypt/archive` as
`0700` and private keys as `0600` `root:root`. A service whose master process
runs as root (nginx, haproxy) can read them directly. For a process that drops
privileges, prefer copying the files in a deploy hook to a service-owned
location; this is portable and keeps `/etc/letsencrypt` private:

```yaml
certbot_certificates:
  - name: example.com
    domains:
      - example.com
    deploy_hooks:
      - install -d -m 0750 -o root -g proxy /etc/proxy/tls
      - >-
        install -m 0640 -o root -g proxy
        /etc/letsencrypt/live/example.com/fullchain.pem
        /etc/proxy/tls/fullchain.pem
      - >-
        install -m 0640 -o root -g proxy
        /etc/letsencrypt/live/example.com/privkey.pem
        /etc/proxy/tls/privkey.pem
      - systemctl reload proxy
```

The target group (`proxy` above) and directory are owned by the consuming
role; create them before the first renewal. The hook only runs after a
renewal (and, on certbot 3.2+, after `certonly`); the consuming role must also
deploy the initial files after the first issuance. On Debian 12 (certbot 2.1)
the initial `certonly` does not run the hook.

ACLs are an alternative when the consumer must read the files in place:

```shell
apt-get install acl
setfacl -m u:proxy:--x \
  /etc/letsencrypt/live /etc/letsencrypt/live/example.com \
  /etc/letsencrypt/archive /etc/letsencrypt/archive/example.com
setfacl -m u:proxy:r-- /etc/letsencrypt/archive/example.com/privkey*.pem
setfacl -m u:proxy:r-- /etc/letsencrypt/archive/example.com/fullchain*.pem
```

ACLs are POSIX.1e, not supported by every filesystem (some network, FUSE or
FAT-based mounts), and `setfacl` needs the `acl` package. Renewal replaces the
archive files, so the ACLs must be re-applied from the deploy hook; applying
them once is not enough. Also grant execute/search permission on the directory
chain, otherwise the ACL on the key is useless. A group-based alternative is
to make the directories traversable (`0750 root:proxy`) and the key readable
(`0640 root:proxy`); certbot preserves the group owner and group mode of
private keys on renewal, but this widens access for every member of that
group.

### Renewal notes

- The initial issuance is not an "auto reload" moment. The nginx role should
  deploy the TLS server block (and reload) after certbot has created the
  lineage. On certbot 3.2+ the directory hooks also run after `certonly`; on
  Debian 12 (certbot 2.1) they only run during `renew`.
- A failing deploy hook is logged by certbot but does not, by itself, make the
  timer unit fail. Monitor the service and the certificates.
- Certificate state lives in `/etc/letsencrypt` (account key, renewal config,
  lineages). Back it up; do not delete it to "reset" a certificate - use
  `certbot delete --cert-name ...` when a lineage is really unwanted.
- `certbot_staging: true` (or `certbot_acme_server` for an internal CA) should
  be used while iterating. Staging and production share the lineage name, so
  switching the CA on an existing lineage requires a forced re-issuance
  (`force: true` or a changed domain set).
- `certbot_no_verify_ssl: true` is for test/private ACME endpoints. On `pypi`
  installs the role also writes `no-verify-ssl = True` to `cli.ini` so
  renewals keep working; on an apt install set `certbot_manage_cli_ini: true`
  or manage `cli.ini` yourself.

## Paths

| Variable | Default |
| --- | --- |
| `certbot_config_dir` | `/etc/letsencrypt` |
| `certbot_work_dir` | `/var/lib/letsencrypt` |
| `certbot_log_dir` | `/var/log/letsencrypt` |
| `certbot_venv_dir` | `/var/lib/certbot/venv` |
| `certbot_dns_credentials_dir` | `<config_dir>/credentials` |

The certbot commands receive `--config-dir`, `--work-dir` and `--logs-dir`
explicitly, so relocating the directories works consistently. For an apt
install with relocated paths the role deploys its own systemd units (shadowing
the package units in `/etc/systemd/system`).

## Nginx composition

```yaml
- name: configure nginx
  ansible.builtin.include_role:
    name: nginx

- name: obtain certificates
  ansible.builtin.include_role:
    name: ak1ra_lab.general.certbot
  vars:
    certbot_email: admin@example.com
    certbot_certificates:
      - name: "{{ nginx_server_name }}"
        domains: "{{ nginx_server_names }}"
    certbot_deploy_hooks:
      - nginx -t && systemctl reload nginx

- name: deploy the TLS server block
  ansible.builtin.include_role:
    name: nginx
  vars:
    nginx_tls: true
```

Point nginx at `/etc/letsencrypt/live/<name>/fullchain.pem` and
`privkey.pem`. The nginx master process runs as root, so the default `0700`
`live` directory is readable; for a non-root consumer use a deploy hook to
copy the files with the required ownership/mode.

## Package files

The systemd unit, `cli.ini` and logrotate snippets are independently written
equivalents of the Debian 13 package files (the cron job is intentionally not
carried over). No certbot or Debian source files are copied into this
collection; the collection remains MIT licensed.

## Testing

Molecule scenarios (Debian 12/13):

- `certbot/apt` - install from apt, issue a certificate against a local Pebble
  ACME server via HTTP-01 with EAB enabled, and verify the renewal
  configuration, per-certificate deploy hook dispatch and timer.
- `certbot/pypi` - install certbot and `certbot-dns-cloudflare` into the venv,
  verify the plugin, credentials, hook, `cli.ini`, logrotate and units.
- `certbot/acmedns` - invoke the acme-dns auth hook against a fake API and
  verify that `example.com`, `*.example.com` and `www.example.com` select the
  correct per-domain accounts, and that an unregistered domain fails clearly.

The Pebble scenario needs no external ACME or DNS-provider access (the
`pebble` package itself comes from the Debian archive). It uses a test domain
(`molecule-certbot.test`) resolved by `pebble-challtestsrv`; no real Let's
Encrypt rate limits are involved.
