#!/usr/bin/env bash

# Minimal acme-dns validation script: register (auto) + update TXT.
#
# Quick start:
#   echo 'ACME_DNS_SERVER_URL=https://auth.example.com:6443' > scripts/acme-dns-register.env
#   ./scripts/acme-dns-register.sh              # auto-register + update with random TXT
#   ./scripts/acme-dns-register.sh "my-value"   # update with explicit TXT

set -o errexit -o nounset

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ENV_FILE="${SCRIPT_DIR}/acme-dns-register.env"

die() { echo "ERROR: ${*}" >&2; exit 1; }
info() { echo "==> ${*}" >&2; }

# --- load .env, env vars override ---
if [[ -f "${ENV_FILE}" ]]; then
    while IFS='=' read -r k v; do
        [[ -z "${k}" || "${k}" == \#* ]] && continue
        v="${v%%\#*}"; v="${v%"${v##*[![:space:]]}"}"
        [[ "${v}" == \"*\" || "${v}" == \'*\' ]] && v="${v:1:-1}"
        [[ -z "${!k:-}" ]] && export "${k}=${v}"
    done < "${ENV_FILE}"
fi

# --- validate ---
if [[ -z "${ACME_DNS_SERVER_URL:-}" ]]; then
    die "ACME_DNS_SERVER_URL is required; set it in ${ENV_FILE} or the environment"
fi

require_cmd() { command -v "${1}" >/dev/null 2>&1 || die "required: ${1}"; }
require_cmd curl
require_cmd jq

# --- persist key=value (sed update or append) ---
set_env() {
    local k="${1}" v="${2}"
    [[ ! -f "${ENV_FILE}" ]] && touch "${ENV_FILE}"
    if grep -qE "^${k}=" "${ENV_FILE}" 2>/dev/null; then
        sed -i "s|^${k}=.*|${k}=${v}|" "${ENV_FILE}"
    else
        echo "${k}=${v}" >> "${ENV_FILE}"
    fi
}

# --- register if needed ---
if [[ -z "${ACME_DNS_USERNAME:-}" || -z "${ACME_DNS_PASSWORD:-}" || -z "${ACME_DNS_SUBDOMAIN:-}" ]]; then
    info "no account found, registering with ${ACME_DNS_SERVER_URL} ..."
    resp="$(curl -fsS -X POST "${ACME_DNS_SERVER_URL}/register")" || die "register failed"
    u="$(echo "${resp}" | jq -r '.username')"
    p="$(echo "${resp}" | jq -r '.password')"
    s="$(echo "${resp}" | jq -r '.subdomain')"
    f="$(echo "${resp}" | jq -r '.fulldomain')"

    set_env ACME_DNS_USERNAME "${u}"
    set_env ACME_DNS_PASSWORD "${p}"
    set_env ACME_DNS_SUBDOMAIN "${s}"
    set_env ACME_DNS_FULLDOMAIN "${f}"

    export ACME_DNS_USERNAME="${u}" ACME_DNS_PASSWORD="${p}"
    export ACME_DNS_SUBDOMAIN="${s}" ACME_DNS_FULLDOMAIN="${f}"

    info "registered: ${f}"
fi

# --- update ---
txt="${1:-}"
if [[ -z "${txt}" ]]; then
    txt="$(LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c43)"
    info "generated random TXT (43 chars)"
fi

info "update: fulldomain=${ACME_DNS_FULLDOMAIN:-${ACME_DNS_SUBDOMAIN}} txt=${txt}"
curl -fsS -X POST \
    -H "X-Api-User: ${ACME_DNS_USERNAME}" \
    -H "X-Api-Key: ${ACME_DNS_PASSWORD}" \
    -d "{\"subdomain\": \"${ACME_DNS_SUBDOMAIN}\", \"txt\": \"${txt}\"}" \
    "${ACME_DNS_SERVER_URL}/update" | jq .
