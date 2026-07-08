#!/usr/bin/env bash

# Download and install python-build-standalone from GitHub releases.
#
# Configuration via environment variables:
#   PYTHON_BUILD_STANDALONE_VERSION   Python version (default: 3.11)
#   PYTHON_BUILD_STANDALONE_PREFIX    Install prefix (default: /usr/local)
#   PYTHON_BUILD_STANDALONE_RELEASE_TAG  Pin a release tag (e.g. 20260112)
#   PYTHON_BUILD_STANDALONE_FORCE     Force reinstall (default: false)
#   PYTHON_BUILD_STANDALONE_ARCH      Override arch (auto-detected via uname -m)
#   PYTHON_BUILD_STANDALONE_EXTRA_PACKAGES  Space-separated pip packages
#   GITHUB_TOKEN                      GitHub API token (avoids rate limits)
#
# Usage: sudo PYTHON_BUILD_STANDALONE_VERSION=3.12 ./python-build-standalone.sh

set -o errexit -o nounset

# --- configuration (override via env) ---
PYTHON_VERSION="${PYTHON_BUILD_STANDALONE_VERSION:-3.11}"
INSTALL_PREFIX="${PYTHON_BUILD_STANDALONE_PREFIX:-/usr/local}"
RELEASE_TAG="${PYTHON_BUILD_STANDALONE_RELEASE_TAG:-}"
FORCE="${PYTHON_BUILD_STANDALONE_FORCE:-false}"
EXTRA_PACKAGES="${PYTHON_BUILD_STANDALONE_EXTRA_PACKAGES:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
ARCH="${PYTHON_BUILD_STANDALONE_ARCH:-}"

readonly REPO="astral-sh/python-build-standalone"
readonly API_BASE="https://api.github.com/repos/${REPO}"
readonly INSTALL_DIR="${INSTALL_PREFIX}/python${PYTHON_VERSION}"
readonly DOWNLOAD_DIR="/tmp/github-releases"
readonly PYTHON_BIN="${INSTALL_DIR}/bin/python${PYTHON_VERSION}"

TEMP_DIR=""

# --- helpers ---
die() {
    echo "ERROR: ${*}" >&2
    exit 1
}
info() { echo "==> ${*}" >&2; }

require_command() {
    local missing=()
    local c
    for c in "${@}"; do
        if ! command -v "${c}" >/dev/null 2>&1; then
            missing+=("${c}")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        die "required command(s) not found: ${missing[*]}"
    fi
}

require_downloader() {
    if command -v curl >/dev/null 2>&1; then
        return 0
    fi
    if command -v wget >/dev/null 2>&1; then
        return 0
    fi
    die "neither curl nor wget is available"
}

cleanup() {
    local exit_code=$?
    if [[ -n "${TEMP_DIR}" ]] && [[ -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
    fi
    exit "${exit_code}"
}

trap cleanup EXIT INT TERM

# --- detect architecture ---
detect_arch() {
    if [[ -n "${ARCH}" ]]; then
        echo "${ARCH}"
        return
    fi
    local machine
    machine="$(uname -m)"
    case "${machine}" in
        x86_64) echo "x86_64" ;;
        aarch64) echo "aarch64" ;;
        *) echo "${machine}" ;;
    esac
}

# --- HTTP fetch (supports curl and wget) ---
http_get() {
    local url="${1}"
    local output="${2:--}"

    if command -v curl >/dev/null 2>&1; then
        local -a opts=(-fsSL)
        [[ -n "${GITHUB_TOKEN}" ]] && opts+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
        opts+=(-o "${output}")
        curl "${opts[@]}" "${url}"
    else
        if [[ -n "${GITHUB_TOKEN}" ]]; then
            wget -q -O "${output}" --header "Authorization: Bearer ${GITHUB_TOKEN}" "${url}"
        else
            wget -q -O "${output}" "${url}"
        fi
    fi
}

# --- fetch release info from GitHub API ---
fetch_release_json() {
    local url
    if [[ -n "${RELEASE_TAG}" ]]; then
        url="${API_BASE}/releases/tags/${RELEASE_TAG}"
    else
        url="${API_BASE}/releases/latest"
    fi
    info "fetching release info: ${url}"
    http_get "${url}"
}

# --- find matching asset URL from release JSON ---
find_asset_url() {
    local arch
    arch="$(detect_arch)"
    jq -r \
        --arg prefix "cpython-${PYTHON_VERSION}." \
        --arg suffix "-${arch}-unknown-linux-gnu-install_only_stripped.tar.gz" \
        '.assets[] | select(.name | startswith($prefix) and endswith($suffix)) | .browser_download_url'
}

main() {
    require_command jq tar
    require_downloader

    if [[ "${FORCE}" != "true" ]] && [[ -x "${PYTHON_BIN}" ]]; then
        if "${PYTHON_BIN}" --version >/dev/null 2>&1; then
            info "already installed: ${PYTHON_BIN}"
            exit 0
        fi
    fi

    if [[ "${FORCE}" == "true" ]] && [[ -d "${INSTALL_DIR}" ]]; then
        info "force reinstall, removing ${INSTALL_DIR}"
        rm -rf "${INSTALL_DIR}"
    fi

    mkdir -p "${DOWNLOAD_DIR}"

    local release_json
    release_json="$(fetch_release_json)" || die "failed to fetch release info"

    local asset_url
    asset_url="$(echo "${release_json}" | find_asset_url | head -1)"

    if [[ -z "${asset_url}" ]]; then
        die "no matching asset found for python ${PYTHON_VERSION} ($(detect_arch))"
    fi

    local asset_name
    asset_name="$(basename "${asset_url}")"
    local asset_path="${DOWNLOAD_DIR}/${asset_name}"

    if [[ ! -f "${asset_path}" ]]; then
        info "downloading: ${asset_url}"
        http_get "${asset_url}" "${asset_path}"
    else
        info "using cached asset: ${asset_path}"
    fi

    info "extracting to ${INSTALL_DIR}"
    mkdir -p "${INSTALL_DIR}"

    TEMP_DIR="$(mktemp -d)"
    tar -xzf "${asset_path}" -C "${TEMP_DIR}"
    mv "${TEMP_DIR}/python/"* "${INSTALL_DIR}/"

    info "bootstrapping pip"
    "${PYTHON_BIN}" -m ensurepip --upgrade

    if [[ -n "${EXTRA_PACKAGES}" ]]; then
        info "installing extra packages: ${EXTRA_PACKAGES}"
        # word-splitting is intentional
        # shellcheck disable=SC2086
        "${PYTHON_BIN}" -m pip install ${EXTRA_PACKAGES}
    fi

    info "python installed: ${PYTHON_BIN}"
    "${PYTHON_BIN}" --version
}

main "${@}"
