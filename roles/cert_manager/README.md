# cert_manager

Manage [cert-manager](https://cert-manager.io/) in a Kubernetes cluster:

- optionally install or upgrade the controller from the official release
  manifest;
- declare ACME `ClusterIssuer` resources and their solver credentials.

The role does **not** create `Ingress` or `Certificate` resources. Applications
(and their Helm charts/owners) own those, usually by annotating an Ingress with
`cert-manager.io/cluster-issuer`. This is intentional: an Ansible role is a poor
owner for per-application resources, and there is no assumption about the
ingress controller (ingress-nginx is no longer maintained; Traefik, HAProxy,
Envoy Gateway, Cilium, ... all work through the same annotations).

## Python dependencies

Install the Kubernetes Python client in the environment that runs Ansible:

```shell
uv add kubernetes          # uv-managed controller
# or: python -m pip install kubernetes
```

The role uses the `kubernetes.core` collection (a normal Ansible collection
dependency, also included in the `ansible` PyPI package). `kubernetes.core.k8s`
requires `kubernetes >= 24.2.0`; `kubernetes.core.k8s_info` is used for the
post-install waits.

Run the role on a host that can read a kubeconfig. The k8s tasks are delegated
to `cert_manager_delegate_to` (default: `localhost`); `cert_manager_kubeconfig`
and `cert_manager_context` are optional and default to `KUBECONFIG` /
`~/.kube/config`. Do not run the role against every cluster node - the resources
are cluster-scoped and applied once.

## Installation

```yaml
cert_manager_install: true
cert_manager_version: v1.18.2
```

The role downloads
`https://github.com/cert-manager/cert-manager/releases/download/<version>/cert-manager.yaml`
into `cert_manager_manifest_cache_dir` and applies it with server-side apply.
It then waits for the `cert-manager-webhook` deployment and the
`clusterissuers.cert-manager.io` CRD. Upgrade by changing the version; CRDs are
included in the release manifest.

If the cluster is managed by Helm or GitOps, leave `cert_manager_install: false`
and let that tool own the controller and CRDs. Do not apply the same objects
from two owners (for example Flux and Ansible): field ownership will fight.

The role intentionally does not install cert-manager with Helm. The official
release manifest is still published and is sufficient for a cluster without a
Helm/GitOps owner; adding Helm would require a `helm` binary on the delegate,
chart version/values handling and a separate CRD upgrade path. In 2026 Helm is
still a common production choice, but it is better left to the tool that
already owns the cluster's releases. The role's value is the ClusterIssuer and
solver-secret layer, which works regardless of how the controller was
installed.

## ClusterIssuers

```yaml
cert_manager_acme_email: admin@example.com

cert_manager_cluster_issuers:
  - name: letsencrypt-prod
    server: https://acme-v02.api.letsencrypt.org/directory
    solver:
      cloudflare:
        api_token: "{{ vault_cloudflare_api_token }}"
        secret_name: cloudflare-main
        dns_zones:
          - example.com

  - name: letsencrypt-staging
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    solver:
      cloudflare:
        secret_name: cloudflare-main

  - name: letsencrypt-http01
    server: https://acme-v02.api.letsencrypt.org/directory
    solver:
      http01:
        ingress_class: traefik
```

Each issuer supports:

| Key | Required | Description |
| --- | --- | --- |
| `name` | yes | `ClusterIssuer` name (unique, DNS label) |
| `server` | yes | ACME directory URL (`https://...`) |
| `email` | no | Overrides `cert_manager_acme_email` |
| `solver` | yes | Exactly one of `cloudflare` (DNS-01) or `http01` |
| `solver.cloudflare.api_token` | conditional | Cloudflare API token; when set the role creates/updates the Secret |
| `solver.cloudflare.secret_name` | no | Secret name; defaults to `<name>-cloudflare` when `api_token` is set. Required when only referencing an existing Secret |
| `solver.cloudflare.dns_zones` | no | `selector.dnsZones`; empty selects all zones the token can edit |
| `solver.http01.ingress_class` | no | `ingressClassName`; empty uses the cluster default class |
| `eab.key_id` | conditional | EAB key ID (required when `eab` is set) |
| `eab.hmac_key` | conditional | CA-provided base64url HMAC key; when set the role creates/updates the Secret |
| `eab.secret_name` | no | EAB Secret name; defaults to `<name>-eab` when `hmac_key` is set. Required when only referencing an existing Secret |
| `profile` | no | Optional ACME profile (`tlsserver`, `shortlived`, ...; cert-manager >= 1.18) |
| `private_key_secret_name` | no | Account key secret name; defaults to `<name>-account-key` |

The role creates only the Secrets that have a credential value. A
`secret_name` without `api_token`/`hmac_key` is a reference to a Secret owned
elsewhere (External Secrets Operator, Sealed Secrets, a GitOps repository, ...).
The same `secret_name` can be shared by several issuers; the values must match.

The role creates the managed solver/EAB Secrets in
`cert_manager_cluster_resource_namespace` (default: the cert-manager
namespace); reference-only Secrets must already exist there. For a
`ClusterIssuer`, cert-manager resolves secret references in its cluster
resource namespace, not in the namespace of the Ingress. If the controller was
installed with a custom `--cluster-resource-namespace`, set
`cert_manager_cluster_resource_namespace` to match.

`cert_manager_namespace` is used for the install wait and the default cluster
resource namespace. The official release manifest always deploys the
controller into `cert-manager`; if you pre-install the controller elsewhere,
leave `cert_manager_install: false` and set the cluster resource namespace
explicitly.

### Cloudflare

`solver.cloudflare.api_token` is rendered into a Secret under the
`api-token` key. Use a scoped token with `Zone:Read` and `DNS:Edit` for the
zones. `solver.cloudflare.dns_zones` becomes that issuer's `selector.dnsZones`
(omit it to select all zones the token can edit). Use the apex zone
(`example.com`), not `*.example.com`.

The default Secret name is `<name>-cloudflare`. Set `secret_name` explicitly
when several issuers share one token, or when the Secret is managed outside
this role. A `secret_name` without `api_token` is reference-only and is not
created or modified by the role.

### External account binding (EAB, for example ZeroSSL)

EAB is a CA feature, not a ZeroSSL feature; ZeroSSL is simply the common public
CA that requires it. EAB belongs to the ACME account, so it is configured per
issuer:

```yaml
cert_manager_cluster_issuers:
  - name: zerossl-prod
    server: https://acme.zerossl.com/v2/DV90
    solver:
      cloudflare:
        secret_name: cloudflare-main
    eab:
      key_id: "..."
      hmac_key: "{{ vault_eab_hmac }}"
      # Optional; defaults to zerossl-prod-eab.
      secret_name: zerossl-eab
```

`hmac_key` is the **base64url-encoded** HMAC key from the CA (the same string
certbot accepts). cert-manager decodes it with `base64.RawURLEncoding`, so do
not pass the raw bytes. HS256 requires at least 32 bytes (RFC 7518);
CA-provided keys satisfy this. When `hmac_key` is empty and `secret_name` is
set, the role only references an existing Secret. Different issuers can use different
EAB credentials; a shared `secret_name` is allowed when they use the same EAB
account.

EAB credentials are tied to the ACME account. Re-creating the account
(deleting the account key Secret) requires a new EAB key/HMAC from the CA.
ZeroSSL's EAB credentials are reusable (since March 2022) and one set is enough
for most deployments; ZeroSSL does not publish a certificate-count quota for
ACME, though it does enforce fair use and limits EAB generation per user/day.

### Why only Cloudflare for DNS-01?

`cert-manager` supports many `dns01` providers, but each one has a different
`spec.acme.solvers[].dns01.<provider>` schema and different credential keys.
This role implements the Cloudflare solver (token Secret + optional
`selector.dnsZones`) and the provider-neutral `http01` solver. That is why
`solver` accepts exactly one of `cloudflare` or `http01`. For another DNS
provider, leave this role's issuer list empty and manage that ClusterIssuer
yourself, or extend the template with the provider's schema and Secret.

### HTTP-01

The HTTP-01 solver creates a temporary Ingress for each challenge. It needs an
ingress controller that serves the challenge path. Set
`solver.http01.ingress_class` explicitly when the cluster has more than one
`IngressClass` or no default; do not rely on an implicit nginx class.

## Rendering manifests

Set `cert_manager_manifest_dir` to an absolute path on the delegate host to
write every managed Secret and ClusterIssuer as YAML (reference-only Secrets
are not rendered):

```yaml
cert_manager_apply: false
cert_manager_manifest_dir: /tmp/cert-manager
```

This is useful for review or for handing the resources to a GitOps repository.
Secret files contain base64-encoded credentials (not encrypted); the directory
is created mode `0700`, Secret files mode `0600`, and the manifests should be
vaulted or deleted after use. With `cert_manager_apply: true` (the default) the
same definitions are also applied to the cluster.

## Ownership and lifecycle

- Pick one owner for the cert-manager controller and for each ClusterIssuer.
  Running this role next to Flux/ArgoCD against the same objects is a conflict,
  not a backup.
- cert-manager creates the ACME account key and the certificates; the role only
  manages issuers and solver/EAB Secrets. Do not delete account-key or
  certificate Secrets to "reset" something.
- Deleting the cert-manager CRDs deletes every `Certificate` and `Order`
  resource with them. Uninstall deliberately.
- Secret rotation is just an apply: change `api_token`/`hmac_key` in the issuer
  definition and re-run; new orders use the new credential, existing
  certificates are unaffected until renewal.
- Monitor `certmanager_certificate_expiration_timestamp_seconds` and
  `certmanager_certificate_ready_status`; an issuer in the cluster does not
  guarantee that individual certificates renew.

## Variables

See `defaults/main.yaml` for the full list. The most important ones:

| Variable | Default | Description |
| --- | --- | --- |
| `cert_manager_install` | `false` | Apply the cert-manager release manifest |
| `cert_manager_version` | empty | Release to install (`v1.18.2`); required when installing |
| `cert_manager_apply` | `true` | Apply the managed solver/EAB Secrets and ClusterIssuers |
| `cert_manager_manifest_dir` | empty | Optional rendered-manifest output directory |
| `cert_manager_delegate_to` | `localhost` | Host that runs the k8s modules |
| `cert_manager_namespace` | `cert-manager` | Controller namespace |
| `cert_manager_cluster_resource_namespace` | `cert_manager_namespace` | Namespace for ClusterIssuer Secret references |
| `cert_manager_acme_email` | empty | Default ACME account email; issuers can override it |
| `cert_manager_cluster_issuers` | `[]` | ClusterIssuer definitions (solver and optional EAB credentials) |

## Testing

`cert_manager/render` renders the Secrets and ClusterIssuers to the controller
and verifies their structure, shared/reference-only Secret handling, solver
references and permissions. It does not need a Kubernetes cluster; the apply
path is covered by using the role against a real cluster.
