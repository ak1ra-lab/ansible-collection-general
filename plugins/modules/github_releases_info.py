from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible_collections.ak1ra_lab.general.plugins.module_utils.github_releases import (
    MICROARCH_LEVEL_ALIASES,
    build_release_api_url,
    build_request_headers,
    normalize_asset,
    normalize_release,
    normalized_request_platform,
    prepare_download_hints,
    select_candidate_assets,
    split_repo,
)

DOCUMENTATION = r"""
---
module: github_releases_info
short_description: Discover and select GitHub release assets for the local platform
description:
  - Query the GitHub releases API for a repository, normalize the release
    assets, and select the best matching asset for the current host.
  - This is a read-only info module. Downloading the selected asset is left to
    follow-up tasks such as M(ansible.builtin.get_url); see the returned
    RV(download_url) and RV(download_checksum) values.
options:
  repo:
    description:
      - Repository in C(OWNER/REPO) format.
    required: true
    type: str
  release_tag:
    description:
      - Query a specific release tag instead of the latest release.
    type: str
    default: ''
  token:
    description:
      - Optional GitHub API token.
    type: str
    no_log: true
  validate_certs:
    description:
      - Validate TLS certificates for GitHub API requests.
    type: bool
    default: true
  timeout:
    description:
      - HTTP timeout in seconds.
    type: int
    default: 30
  require_digest:
    description:
      - Fail when neither an explicit checksum nor a digest provided by GitHub
        is available for the selected asset, so callers can always pass
        RV(download_checksum) to M(ansible.builtin.get_url).
    type: bool
    default: true
  asset_checksum:
    description:
      - Explicit checksum string for the selected asset. Accepts
        C(algorithm:value) or a hexadecimal digest whose length identifies the
        algorithm. Returned normalized as C(algorithm:value).
    type: str
    default: ''
  asset_url:
    description:
      - Exact browser download URL selector.
    type: str
    default: ''
  asset_name:
    description:
      - Exact asset filename selector.
    type: str
    default: ''
  asset_name_regex:
    description:
      - Regular expression applied to asset filenames.
    type: str
    default: ''
  asset_name_contains:
    description:
      - Required case-insensitive substrings applied to asset filenames.
    type: list
    elements: str
    default: []
  asset_os:
    description:
      - Override the requested operating system token.
    type: str
    default: ''
  asset_arch:
    description:
      - Override the requested architecture token.
    type: str
    default: ''
  asset_distro:
    description:
      - Override the requested distribution token.
    type: str
    default: ''
  asset_libc:
    description:
      - Override the requested Linux libc token.
    type: str
    default: ''
  asset_microarch:
    description:
      - Requested CPU microarchitecture level, for example C(x86-64-v3).
        Shorthands C(v3) and C(3) are accepted.
      - Assets tagged with a different level (for example C(x86-64-v4)) are
        filtered out; assets tagged with the requested level are preferred
        over untagged (baseline) assets.
      - Pair with the M(ak1ra_lab.general.cpu_info) module, whose detected
        level can be passed here.
    type: str
    default: ''
  preferred_asset_families:
    description:
      - Asset family preference order used during automatic narrowing.
    type: list
    elements: str
    default:
      - deb
      - archive
notes:
  - Assets tagged with a microarchitecture level are only recognized by full
    filename tokens such as C(x86-64-v3) or C(amd64_v3); pass feature tokens
    like C(avx2) via O(asset_name_contains) instead.
  - Supports check mode; the API query runs in check mode as usual for info
    modules.
author:
  - ak1ra
"""

EXAMPLES = r"""
- name: Inspect the latest release without downloading
  ak1ra_lab.general.github_releases_info:
    repo: sharkdp/bat

- name: Select an asset and download it with get_url
  ak1ra_lab.general.github_releases_info:
    repo: sharkdp/bat
    asset_name_regex: 'linux.*x86_64.*\.tar\.gz$'
  register: bat_release

- name: Download the selected asset
  ansible.builtin.get_url:
    url: "{{ bat_release.download_url }}"
    dest: /tmp/{{ bat_release.selected_asset.name }}
    checksum: "{{ bat_release.download_checksum }}"
    mode: "0644"

- name: Select an asset matching the CPU microarchitecture level
  ak1ra_lab.general.github_releases_info:
    repo: example/tool
    asset_microarch: "{{ ansible_facts['cpu']['microarch_level'] }}"
"""

RETURN = r"""
owner:
  description: Repository owner.
  returned: always
  type: str
name:
  description: Repository name.
  returned: always
  type: str
repo:
  description: Repository in C(OWNER/REPO) format.
  returned: always
  type: str
release_api_url:
  description: GitHub releases API URL that was queried.
  returned: always
  type: str
release:
  description: Normalized release metadata.
  returned: always
  type: dict
assets:
  description: Normalized release asset metadata.
  returned: always
  type: list
candidate_assets:
  description: Assets that remain after selection filtering.
  returned: always
  type: list
selected_family:
  description: Asset family chosen from O(preferred_asset_families).
  returned: always
  type: str
selected_asset:
  description: Final selected asset.
  returned: always
  type: dict
download_url:
  description:
    - Browser download URL of the selected asset, ready for
      M(ansible.builtin.get_url).
  returned: always
  type: str
download_checksum:
  description:
    - Checksum for the selected asset in C(algorithm:value) form, ready for
      M(ansible.builtin.get_url). Empty when no checksum is available.
  returned: always
  type: str
download_verification:
  description:
    - Checksum source for the selected asset. C(explicit) when
      O(asset_checksum) was provided, C(github-digest) when the GitHub asset
      digest field is available, C(none) otherwise.
  returned: always
  type: str
  sample: github-digest
requested_os:
  description: Operating system token used during selection.
  returned: always
  type: str
requested_arch:
  description: Architecture token used during selection.
  returned: always
  type: str
requested_distro:
  description: Distribution token used during selection.
  returned: always
  type: str
requested_libc:
  description: Linux libc token used during selection.
  returned: always
  type: str
requested_microarch:
  description: Microarchitecture level token used during selection.
  returned: always
  type: str
  sample: x86-64-v3
"""


def fail_http_error(module: AnsibleModule, exc: Exception, context: str) -> Any:
    status = getattr(exc, "code", None)
    response = ""
    reader = getattr(exc, "read", None)
    if callable(reader):
        try:
            raw_response = reader()
            if isinstance(raw_response, (bytes, bytearray)):
                response = raw_response.decode("utf-8", errors="replace")
            else:
                response = str(raw_response)
        except Exception:  # noqa: BLE001 - best-effort error body read
            response = ""

    return module.fail_json(
        msg=f"{context}: {exc}",
        status=status,
        response=response,
    )


def query_release_metadata(
    module: AnsibleModule,
    release_api_url: str,
    request_headers: dict[str, str],
) -> dict[str, Any]:
    try:
        response = open_url(
            release_api_url,
            headers=request_headers,
            method="GET",
            validate_certs=module.params["validate_certs"],
            timeout=module.params["timeout"],
        )
        try:
            return json.loads(response.read())
        finally:
            response.close()
    except HTTPError as exc:
        return fail_http_error(module, exc, "failed to query GitHub release metadata")
    except URLError as exc:
        return module.fail_json(msg=f"failed to query GitHub release metadata: {exc}")
    except ValueError as exc:
        return module.fail_json(msg=f"failed to decode GitHub release metadata: {exc}")

    return module.fail_json(msg="failed to query GitHub release metadata")


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "repo": {"type": "str", "required": True},
            "release_tag": {"type": "str", "default": ""},
            "token": {"type": "str", "default": "", "no_log": True},
            "validate_certs": {"type": "bool", "default": True},
            "timeout": {"type": "int", "default": 30},
            "require_digest": {"type": "bool", "default": True},
            "asset_checksum": {"type": "str", "default": ""},
            "asset_url": {"type": "str", "default": ""},
            "asset_name": {"type": "str", "default": ""},
            "asset_name_regex": {"type": "str", "default": ""},
            "asset_name_contains": {"type": "list", "elements": "str", "default": []},
            "asset_os": {"type": "str", "default": ""},
            "asset_arch": {"type": "str", "default": ""},
            "asset_distro": {"type": "str", "default": ""},
            "asset_libc": {"type": "str", "default": ""},
            "asset_microarch": {"type": "str", "default": ""},
            "preferred_asset_families": {
                "type": "list",
                "elements": "str",
                "default": ["deb", "archive"],
            },
        },
        supports_check_mode=True,
    )

    params = module.params
    if params["asset_url"] and params["asset_name"]:
        module.fail_json(msg="asset_url and asset_name are mutually exclusive exact selectors")

    try:
        owner, name = split_repo(params["repo"])
    except ValueError as exc:
        module.fail_json(msg=str(exc))

    release_api_url = build_release_api_url(params["repo"], params["release_tag"])
    request_headers = build_request_headers(params["token"])
    requested_platform = normalized_request_platform(params)

    requested_microarch = requested_platform["requested_microarch"]
    if requested_microarch and requested_microarch not in MICROARCH_LEVEL_ALIASES:
        module.fail_json(
            msg=(
                f"asset_microarch must be empty or one of {', '.join(MICROARCH_LEVEL_ALIASES)}"
                " (shorthands v1..v4 are accepted)"
            )
        )

    release_raw = query_release_metadata(module, release_api_url, request_headers)
    release = normalize_release(release_raw, params["repo"], release_api_url)
    assets = [normalize_asset(asset_raw) for asset_raw in release_raw.get("assets") or []]

    try:
        candidate_assets, selected_family, selected_asset = select_candidate_assets(
            params["repo"],
            assets,
            params,
            requested_platform,
        )
        download_hints = prepare_download_hints(params, selected_asset)
    except (LookupError, RuntimeError, ValueError) as exc:
        module.fail_json(msg=str(exc), release=release, assets=assets)

    result: dict[str, Any] = {
        "owner": owner,
        "name": name,
        "repo": params["repo"],
        "release_api_url": release_api_url,
        "release": release,
        "assets": assets,
        "candidate_assets": candidate_assets,
        "selected_family": selected_family,
        "selected_asset": selected_asset,
        "download_url": download_hints["download_url"],
        "download_checksum": download_hints["download_checksum"],
        "download_verification": download_hints["download_verification"],
    }
    result.update(requested_platform)

    if params["require_digest"] and not result["download_checksum"]:
        module.fail_json(
            msg=(
                "require_digest is true but neither asset_checksum nor the GitHub asset digest field "
                f"is available for {selected_asset['name']}."
            ),
            **result,
        )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
