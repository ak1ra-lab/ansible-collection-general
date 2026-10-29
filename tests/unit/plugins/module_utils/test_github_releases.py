# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the github_releases_info module_utils.

These cover the pure normalization/selection helpers; the module itself is
exercised by Molecule scenarios that need a live GitHub API.
"""

from __future__ import annotations

from typing import Any

import pytest
from ansible_collections.ak1ra_lab.general.plugins.module_utils import github_releases as gh


def asset(name: str, **overrides: Any) -> dict[str, Any]:
    raw = {
        "id": 1,
        "name": name,
        "label": "",
        "size": 1024,
        "content_type": "application/octet-stream",
        "state": "uploaded",
        "browser_download_url": f"https://example.invalid/{name}",
        "download_count": 0,
        "created_at": "",
        "updated_at": "",
        "digest": "",
    }
    raw.update(overrides)
    return gh.normalize_asset(raw)


def test_split_repo() -> None:
    assert gh.split_repo("ak1ra-lab/tool") == ("ak1ra-lab", "tool")
    assert gh.split_repo("/ak1ra-lab/tool/") == ("ak1ra-lab", "tool")

    with pytest.raises(ValueError, match="OWNER/REPO"):
        gh.split_repo("tool")


def test_build_release_api_url() -> None:
    assert gh.build_release_api_url("ak1ra-lab/tool", "") == (
        "https://api.github.com/repos/ak1ra-lab/tool/releases/latest"
    )
    assert gh.build_release_api_url("ak1ra-lab/tool", "v1.2.3") == (
        "https://api.github.com/repos/ak1ra-lab/tool/releases/tags/v1.2.3"
    )


def test_build_request_headers() -> None:
    assert gh.build_request_headers("") == {
        "Accept": gh.API_ACCEPT,
        "X-GitHub-Api-Version": gh.API_VERSION,
    }
    assert gh.build_request_headers("token")["Authorization"] == "Bearer token"


def test_ensure_string_list() -> None:
    assert gh.ensure_string_list(None) == []
    assert gh.ensure_string_list("linux") == ["linux"]
    assert gh.ensure_string_list("['linux', 'amd64']") == ["linux", "amd64"]
    assert gh.ensure_string_list(["linux"]) == ["linux"]


def test_normalize_microarch() -> None:
    assert gh.normalize_microarch("3") == "x86-64-v3"
    assert gh.normalize_microarch("v3") == "x86-64-v3"
    assert gh.normalize_microarch("x86-64-v4") == "x86-64-v4"
    assert gh.normalize_microarch("") == ""


def test_detect_file_extension_prefers_compound_suffixes() -> None:
    assert gh.detect_file_extension("tool_1.2.3_linux_amd64.tar.gz") == ".tar.gz"
    assert gh.detect_file_extension("tool_1.2.3_linux_amd64.deb") == ".deb"
    assert gh.detect_file_extension("tool_1.2.3_checksums.txt") == ".txt"
    assert gh.detect_file_extension("tool") == ""


def test_detect_package_and_archive_type() -> None:
    assert gh.detect_package_type("tool.deb") == "deb"
    assert gh.detect_package_type("tool.rpm") == "rpm"
    assert gh.detect_package_type("tool.apk") == "apk"
    assert gh.detect_package_type("tool.pkg.tar.zst") == "pkg"
    assert gh.detect_package_type("tool.tar.gz") == ""
    assert gh.detect_archive_type("tool.tar.gz") == "tar.gz"
    assert gh.detect_archive_type("tool.tgz") == "tar.gz"
    assert gh.detect_archive_type("tool.zip") == "zip"
    assert gh.detect_archive_type("tool.deb") == ""


def test_normalize_asset_infers_platform_tokens() -> None:
    normalized = asset(
        "tool_1.2.3_linux_amd64_x86-64-v3.tar.gz",
        digest="sha256:" + "a" * 64,
    )

    assert normalized["file_extension"] == ".tar.gz"
    assert normalized["archive_type"] == "tar.gz"
    assert normalized["asset_family"] == "archive"
    assert normalized["inferred_os"] == ["linux"]
    assert normalized["inferred_arch"] == ["amd64"]
    assert normalized["inferred_microarch"] == ["x86-64-v3"]
    assert normalized["digest_algorithm"] == "sha256"
    assert normalized["digest_value"] == "a" * 64


def test_microarch_token_does_not_match_version_prefix() -> None:
    """`tool-amd64-v1.19.30.deb` is a version, not an x86-64-v1 asset."""
    assert gh.infer_microarch_matches("tool-amd64-v1.19.30.deb") == []
    assert gh.infer_microarch_matches("tool-amd64-v3.deb") == ["x86-64-v3"]


def test_asset_matches_platform_only_rejects_conflicting_tokens() -> None:
    linux_amd64 = asset("tool_linux_amd64.tar.gz")
    requested = {
        "requested_os": "linux",
        "requested_arch": "amd64",
        "requested_distro": "",
        "requested_libc": "",
        "requested_microarch": "",
    }
    assert gh.asset_matches_platform(linux_amd64, requested)

    requested["requested_arch"] = "arm64"
    assert not gh.asset_matches_platform(linux_amd64, requested)


def test_select_candidate_assets_requires_a_unique_match() -> None:
    linux = asset("tool_linux_amd64.tar.gz", browser_download_url="https://example.invalid/linux")
    darwin = asset("tool_darwin_amd64.tar.gz", browser_download_url="https://example.invalid/darwin")
    platform = {
        "requested_os": "linux",
        "requested_arch": "amd64",
        "requested_distro": "",
        "requested_libc": "",
        "requested_microarch": "",
    }

    candidates, family, selected = gh.select_candidate_assets(
        "ak1ra-lab/tool",
        [linux, darwin],
        {},
        platform,
    )

    assert candidates == [linux]
    assert family == ""
    assert selected["name"] == "tool_linux_amd64.tar.gz"


def test_select_candidate_assets_rejects_ambiguous_matches() -> None:
    assets = [asset("tool_linux_amd64.tar.gz"), asset("tool_linux_amd64.zip")]
    platform = {
        "requested_os": "linux",
        "requested_arch": "amd64",
        "requested_distro": "",
        "requested_libc": "",
        "requested_microarch": "",
    }

    with pytest.raises(RuntimeError, match="Multiple GitHub release assets"):
        gh.select_candidate_assets("ak1ra-lab/tool", assets, {}, platform)


def test_select_candidate_assets_reports_no_match() -> None:
    platform = {
        "requested_os": "linux",
        "requested_arch": "amd64",
        "requested_distro": "",
        "requested_libc": "",
        "requested_microarch": "",
    }

    with pytest.raises(LookupError, match="No GitHub release assets matched"):
        gh.select_candidate_assets("ak1ra-lab/tool", [asset("tool_darwin_arm64.tar.gz")], {}, platform)


def test_prepare_download_hints_prefers_explicit_checksum() -> None:
    selected = asset(
        "tool.deb",
        browser_download_url="https://example.invalid/tool.deb",
        digest="sha256:" + "b" * 64,
    )

    hints = gh.prepare_download_hints({"asset_checksum": "sha512:" + "C" * 128}, selected)

    assert hints["download_url"] == "https://example.invalid/tool.deb"
    assert hints["download_checksum"] == "sha512:" + "c" * 128
    assert hints["download_verification"] == "explicit"


def test_prepare_download_hints_uses_github_digest() -> None:
    selected = asset("tool.deb", digest="sha256:" + "b" * 64)

    hints = gh.prepare_download_hints({}, selected)

    assert hints["download_checksum"] == "sha256:" + "b" * 64
    assert hints["download_verification"] == "github-digest"


def test_checksum_parts() -> None:
    assert gh.checksum_parts("sha256:" + "A" * 64) == ("sha256", "a" * 64)
    assert gh.checksum_parts("a" * 64) == ("sha256", "a" * 64)
    assert gh.checksum_parts("a" * 40) == ("sha1", "a" * 40)

    with pytest.raises(ValueError, match="checksum"):
        gh.checksum_parts("not-a-digest")
