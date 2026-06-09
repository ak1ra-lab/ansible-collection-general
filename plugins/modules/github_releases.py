from __future__ import annotations

import json
import os
import shutil
import tempfile
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible_collections.ak1ra_lab.general.plugins.module_utils.github_releases import (
    build_release_api_url,
    build_request_headers,
    file_matches_checksum,
    normalize_asset,
    normalize_release,
    normalized_request_platform,
    prepare_download_details,
    select_candidate_assets,
    split_repo,
)

DOWNLOAD_BLOCK_SIZE = 1024 * 1024

DOCUMENTATION = r"""
---
module: github_releases
short_description: Discover, select, and optionally download GitHub release assets
description:
  - Query the GitHub releases API for a repository, normalize release assets,
    select a matching asset, and optionally download it on the managed host.
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
      - Validate TLS certificates for GitHub API and asset downloads.
    type: bool
    default: true
  timeout:
    description:
      - HTTP timeout in seconds.
    type: int
    default: 30
  download:
    description:
      - Download the selected asset on the managed host.
    type: bool
    default: true
  download_dir:
    description:
      - Base directory for downloaded assets.
    type: path
    default: /tmp/github-releases
  download_mode:
    description:
      - File mode for downloaded assets.
    type: str
    default: '0644'
  force_download:
    description:
      - Force a fresh asset download even when the destination already exists.
    type: bool
    default: false
  require_digest:
    description:
      - Require either an explicit checksum or a digest provided by GitHub.
    type: bool
    default: true
  asset_checksum:
    description:
      - Explicit checksum string for the selected asset.
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
  preferred_asset_families:
    description:
      - Asset family preference order used during automatic narrowing.
    type: list
    elements: str
    default:
      - deb
      - archive
author:
  - ak1ra
"""

EXAMPLES = r"""
- name: Inspect the latest release without downloading
  ak1ra_lab.general.github_releases:
    repo: sharkdp/bat
    download: false

- name: Download a selected release asset
  ak1ra_lab.general.github_releases:
    repo: sharkdp/bat
    asset_name_regex: 'linux.*amd64.*\.deb$'
"""

RETURN = r"""
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
selected_asset:
  description: Final selected asset.
  returned: always
  type: dict
download_path:
  description: Download destination path when download is enabled.
  returned: always
  type: str
download_checksum:
  description: Checksum used for verification when available.
  returned: always
  type: str
download_verification:
  description: Verification mode for the selected asset.
  returned: always
  type: str
download_result:
  description: Download execution details when download is enabled.
  returned: always
  type: dict
"""


def fail_http_error(module: AnsibleModule, exc: Exception, context: str) -> None:
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
        except Exception:
            response = ""

    module.fail_json(
        msg="{0}: {1}".format(context, exc),
        status=status,
        response=response,
    )


def query_release_metadata(
    module: AnsibleModule,
    release_api_url: str,
    request_headers: Dict[str, str],
) -> Dict[str, Any]:
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
        fail_http_error(module, exc, "failed to query GitHub release metadata")
    except URLError as exc:
        module.fail_json(msg="failed to query GitHub release metadata: {0}".format(exc))
    except ValueError as exc:
        module.fail_json(
            msg="failed to decode GitHub release metadata: {0}".format(exc)
        )

    module.fail_json(msg="failed to query GitHub release metadata")


def download_selected_asset(
    module: AnsibleModule,
    selected_asset: Dict[str, Any],
    request_headers: Dict[str, str],
    download_details: Dict[str, str],
) -> Tuple[bool, Dict[str, Any]]:
    download_path = download_details["download_path"]
    download_checksum = download_details["download_checksum"]

    os.makedirs(os.path.dirname(download_path), mode=0o755, exist_ok=True)

    if os.path.exists(download_path) and not module.params["force_download"]:
        if not download_checksum:
            return False, {
                "dest": download_path,
                "skipped": True,
                "reason": "destination exists and force_download is false",
            }

        try:
            if file_matches_checksum(download_path, download_checksum):
                return False, {
                    "dest": download_path,
                    "skipped": True,
                    "reason": "destination already matches checksum",
                }
        except ValueError as exc:
            module.fail_json(msg=str(exc))

    temp_file = None
    response = None
    try:
        response = open_url(
            selected_asset["browser_download_url"],
            headers=request_headers,
            method="GET",
            validate_certs=module.params["validate_certs"],
            timeout=module.params["timeout"],
        )

        file_descriptor, temp_file = tempfile.mkstemp(
            dir=os.path.dirname(download_path),
            prefix=".github-release-",
            suffix=".tmp",
        )
        with os.fdopen(file_descriptor, "wb") as handle:
            shutil.copyfileobj(response, handle, length=DOWNLOAD_BLOCK_SIZE)

        if download_checksum:
            try:
                if not file_matches_checksum(temp_file, download_checksum):
                    module.fail_json(
                        msg="downloaded asset checksum did not match expected value",
                        dest=download_path,
                        checksum=download_checksum,
                    )
            except ValueError as exc:
                module.fail_json(msg=str(exc))

        os.replace(temp_file, download_path)
        temp_file = None
        os.chmod(download_path, int(str(module.params["download_mode"]), 8))
        return True, {
            "dest": download_path,
            "size": os.path.getsize(download_path),
            "url": selected_asset["browser_download_url"],
        }
    except HTTPError as exc:
        fail_http_error(module, exc, "failed to download GitHub release asset")
    except URLError as exc:
        module.fail_json(msg="failed to download GitHub release asset: {0}".format(exc))
    finally:
        if response is not None:
            response.close()
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

    module.fail_json(msg="failed to download GitHub release asset")


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "repo": {"type": "str", "required": True},
            "release_tag": {"type": "str", "default": ""},
            "token": {"type": "str", "default": "", "no_log": True},
            "validate_certs": {"type": "bool", "default": True},
            "timeout": {"type": "int", "default": 30},
            "download": {"type": "bool", "default": True},
            "download_dir": {"type": "path", "default": "/tmp/github-releases"},
            "download_mode": {"type": "str", "default": "0644"},
            "force_download": {"type": "bool", "default": False},
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
            "preferred_asset_families": {
                "type": "list",
                "elements": "str",
                "default": ["deb", "archive"],
            },
        },
        supports_check_mode=False,
    )

    params = module.params
    if params["asset_url"] and params["asset_name"]:
        module.fail_json(
            msg="asset_url and asset_name are mutually exclusive exact selectors"
        )

    try:
        owner, name = split_repo(params["repo"])
    except ValueError as exc:
        module.fail_json(msg=str(exc))

    release_api_url = build_release_api_url(params["repo"], params["release_tag"])
    request_headers = build_request_headers(params["token"])
    requested_platform = normalized_request_platform(params)

    release_raw = query_release_metadata(module, release_api_url, request_headers)
    release = normalize_release(release_raw, params["repo"], release_api_url)
    assets = [
        normalize_asset(asset_raw) for asset_raw in release_raw.get("assets") or []
    ]

    try:
        candidate_assets, selected_family, selected_asset = select_candidate_assets(
            params["repo"],
            assets,
            params,
            requested_platform,
        )
    except (LookupError, RuntimeError, ValueError) as exc:
        module.fail_json(msg=str(exc), release=release, assets=assets)

    result: Dict[str, Any] = {
        "changed": False,
        "owner": owner,
        "name": name,
        "repo": params["repo"],
        "release_api_url": release_api_url,
        "release": release,
        "assets": assets,
        "candidate_assets": candidate_assets,
        "selected_family": selected_family,
        "selected_asset": selected_asset,
        "download_path": "",
        "download_checksum": "",
        "download_verification": "not-requested",
        "download_result": {},
    }
    result.update(requested_platform)

    if params["download"]:
        download_details = prepare_download_details(
            params, owner, name, release, selected_asset
        )
        result.update(download_details)

        if params["require_digest"] and not download_details["download_checksum"]:
            module.fail_json(
                msg=(
                    "require_digest is true but neither asset_checksum nor the GitHub asset digest field "
                    "is available for {0}."
                ).format(selected_asset["name"]),
                **result,
            )

        changed, download_result = download_selected_asset(
            module,
            selected_asset,
            request_headers,
            download_details,
        )
        result["changed"] = changed
        result["download_result"] = download_result

    module.exit_json(**result)


if __name__ == "__main__":
    main()
