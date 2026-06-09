from __future__ import annotations

import ast
import hashlib
import os
import platform
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

API_BASE_URL = "https://api.github.com"
API_ACCEPT = "application/vnd.github+json"
API_VERSION = "2026-03-10"

OS_FACT_MAP = {
    "linux": "linux",
    "darwin": "darwin",
    "freebsd": "freebsd",
    "openbsd": "openbsd",
    "netbsd": "netbsd",
    "win32nt": "windows",
}

ARCH_FACT_MAP = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "i386": "386",
    "i686": "386",
    "arm64": "arm64",
    "aarch64": "arm64",
    "armv7": "armv7",
    "armv7l": "armv7",
    "armv6": "armv6",
    "armv6l": "armv6",
    "ppc64le": "ppc64le",
    "ppc64el": "ppc64le",
    "riscv64": "riscv64",
    "s390x": "s390x",
}

DISTRO_FACT_MAP = {
    "debian": "debian",
    "ubuntu": "ubuntu",
    "redhat": "rhel",
    "red hat enterprise linux": "rhel",
    "centos": "centos",
    "rocky": "rocky",
    "almalinux": "almalinux",
    "fedora": "fedora",
    "alpine": "alpine",
    "opensuse": "suse",
    "opensuse leap": "suse",
    "suse": "suse",
}

LIBC_FACT_MAP = {
    "alpine": "musl",
    "debian": "gnu",
    "ubuntu": "gnu",
    "redhat": "gnu",
    "red hat enterprise linux": "gnu",
    "centos": "gnu",
    "rocky": "gnu",
    "almalinux": "gnu",
    "fedora": "gnu",
    "opensuse": "gnu",
    "opensuse leap": "gnu",
    "suse": "gnu",
}

OS_ALIAS_MAP = {
    "linux": ["linux"],
    "darwin": ["darwin", "macos", "osx", "mac"],
    "windows": ["windows", "win32", "win64"],
    "freebsd": ["freebsd"],
    "openbsd": ["openbsd"],
    "netbsd": ["netbsd"],
}

ARCH_ALIAS_MAP = {
    "amd64": ["amd64", "x86_64", "x64", "64bit"],
    "386": ["386", "i386", "i686", "32bit"],
    "arm64": ["arm64", "aarch64", "armv8"],
    "armv7": ["armv7", "armv7l", "armhf"],
    "armv6": ["armv6", "armv6l", "armel"],
    "ppc64le": ["ppc64le", "ppc64el"],
    "riscv64": ["riscv64"],
    "s390x": ["s390x"],
}

LIBC_ALIAS_MAP = {
    "gnu": ["gnu", "glibc"],
    "musl": ["musl"],
}

DISTRO_ALIAS_MAP = {
    "debian": ["debian"],
    "ubuntu": ["ubuntu"],
    "rhel": ["rhel", "redhat", "el"],
    "centos": ["centos"],
    "rocky": ["rocky"],
    "almalinux": ["almalinux"],
    "fedora": ["fedora"],
    "alpine": ["alpine"],
    "suse": ["suse", "opensuse"],
}

CHECKSUM_LENGTH_TO_ALGORITHM = {
    32: "md5",
    40: "sha1",
    56: "sha224",
    64: "sha256",
    96: "sha384",
    128: "sha512",
}

ASSET_EXTENSION_PATTERN = re.compile(
    r"(\.pkg\.tar\.zst|\.pkg\.tar\.xz|\.tar\.gz|\.tar\.xz|\.tar\.bz2|\.tgz|\.tbz2|\.txz|\.deb|\.rpm|\.apk|\.zip)$"
)
SIMPLE_EXTENSION_PATTERN = re.compile(r"\.[^.]+$")
HEX_DIGEST_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


def lower_string(value: Any) -> str:
    return str(value or "").lower()


def ensure_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            for parser in (lambda raw: ast.literal_eval(raw),):
                try:
                    parsed = parser(stripped)
                except (SyntaxError, ValueError):
                    continue

                if isinstance(parsed, (list, tuple)):
                    return [str(item) for item in parsed]
        return [value]
    return [str(item) for item in value]


def split_repo(repo: str) -> Tuple[str, str]:
    parts = [part for part in str(repo).strip("/").split("/") if part]
    if len(parts) != 2:
        raise ValueError("repo must be in OWNER/REPO format")
    return parts[0], parts[1]


def build_release_api_url(repo: str, release_tag: str) -> str:
    suffix = "tags/{0}".format(release_tag) if release_tag else "latest"
    return "{0}/repos/{1}/releases/{2}".format(API_BASE_URL, repo, suffix)


def build_request_headers(token: str) -> Dict[str, str]:
    headers = {
        "Accept": API_ACCEPT,
        "X-GitHub-Api-Version": API_VERSION,
    }
    if token:
        headers["Authorization"] = "Bearer {0}".format(token)
    return headers


def parse_os_release() -> Dict[str, str]:
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        if not os.path.exists(path):
            continue

        data = {}
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                data[key.lower()] = value.strip().strip('"').strip("'")
        return data

    return {}


def detect_local_platform_facts() -> Dict[str, str]:
    os_release = parse_os_release()
    return {
        "system": lower_string(platform.system()),
        "architecture": lower_string(platform.machine()),
        "distribution": lower_string(os_release.get("id", "")),
    }


def normalized_request_platform(
    params: Mapping[str, Any],
    facts: Optional[Mapping[str, Any]] = None,
) -> Dict[str, str]:
    detected_facts = detect_local_platform_facts()
    if facts:
        detected_facts.update(
            {
                "system": lower_string(facts.get("system")) or detected_facts["system"],
                "architecture": lower_string(facts.get("architecture"))
                or detected_facts["architecture"],
                "distribution": lower_string(facts.get("distribution"))
                or detected_facts["distribution"],
            }
        )

    system = detected_facts["system"]
    architecture = detected_facts["architecture"]
    distribution = detected_facts["distribution"]

    requested_os = lower_string(params.get("asset_os")) or OS_FACT_MAP.get(system, "")
    requested_arch = lower_string(params.get("asset_arch")) or ARCH_FACT_MAP.get(
        architecture, ""
    )
    requested_distro = lower_string(params.get("asset_distro")) or DISTRO_FACT_MAP.get(
        distribution, ""
    )

    requested_libc = lower_string(params.get("asset_libc"))
    if not requested_libc and system == "linux":
        requested_libc = LIBC_FACT_MAP.get(distribution, "gnu")

    return {
        "requested_os": requested_os,
        "requested_arch": requested_arch,
        "requested_distro": requested_distro,
        "requested_libc": requested_libc,
    }


def detect_file_extension(name_lower: str) -> str:
    match = ASSET_EXTENSION_PATTERN.search(name_lower)
    if match:
        return match.group(0)

    match = SIMPLE_EXTENSION_PATTERN.search(name_lower)
    return match.group(0) if match else ""


def detect_package_type(name_lower: str) -> str:
    if name_lower.endswith(".deb"):
        return "deb"
    if name_lower.endswith(".rpm"):
        return "rpm"
    if name_lower.endswith(".apk"):
        return "apk"
    if name_lower.endswith(".pkg.tar.zst") or name_lower.endswith(".pkg.tar.xz"):
        return "pkg"
    return ""


def detect_archive_type(name_lower: str) -> str:
    if name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz"):
        return "tar.gz"
    if name_lower.endswith(".tar.xz") or name_lower.endswith(".txz"):
        return "tar.xz"
    if name_lower.endswith(".tar.bz2") or name_lower.endswith(".tbz2"):
        return "tar.bz2"
    if name_lower.endswith(".zip"):
        return "zip"
    return ""


def parse_digest(digest: str) -> Tuple[str, str, str]:
    digest = str(digest or "")
    if ":" not in digest:
        return digest, "", ""

    algorithm, value = digest.split(":", 1)
    return digest, lower_string(algorithm), value.strip()


def infer_alias_matches(
    name_lower: str, alias_map: Mapping[str, Sequence[str]]
) -> List[str]:
    matches = []
    for canonical, aliases in alias_map.items():
        for alias in aliases:
            pattern = r"(^|[._-]){0}([._-]|$)".format(re.escape(alias))
            if re.search(pattern, name_lower):
                matches.append(canonical)
                break
    return matches


def normalize_release(
    release_raw: Mapping[str, Any], repo: str, api_url: str
) -> Dict[str, Any]:
    assets_raw = release_raw.get("assets") or []
    return {
        "repo": repo,
        "api_url": api_url,
        "id": release_raw.get("id") or "",
        "tag_name": release_raw.get("tag_name") or "",
        "name": release_raw.get("name") or "",
        "html_url": release_raw.get("html_url") or "",
        "draft": bool(release_raw.get("draft", False)),
        "prerelease": bool(release_raw.get("prerelease", False)),
        "published_at": release_raw.get("published_at") or "",
        "target_commitish": release_raw.get("target_commitish") or "",
        "asset_count": len(assets_raw),
    }


def normalize_asset(asset_raw: Mapping[str, Any]) -> Dict[str, Any]:
    name = str(asset_raw.get("name") or "")
    name_lower = name.lower()
    digest, digest_algorithm, digest_value = parse_digest(asset_raw.get("digest") or "")
    package_type = detect_package_type(name_lower)
    archive_type = detect_archive_type(name_lower)

    return {
        "id": asset_raw.get("id") or "",
        "name": name,
        "label": asset_raw.get("label") or "",
        "size": int(asset_raw.get("size") or 0),
        "content_type": asset_raw.get("content_type") or "",
        "state": asset_raw.get("state") or "",
        "browser_download_url": asset_raw.get("browser_download_url") or "",
        "download_count": int(asset_raw.get("download_count") or 0),
        "created_at": asset_raw.get("created_at") or "",
        "updated_at": asset_raw.get("updated_at") or "",
        "digest": digest,
        "digest_algorithm": digest_algorithm,
        "digest_value": digest_value,
        "file_extension": detect_file_extension(name_lower),
        "package_type": package_type,
        "archive_type": archive_type,
        "asset_family": package_type or ("archive" if archive_type else "raw"),
        "inferred_os": infer_alias_matches(name_lower, OS_ALIAS_MAP),
        "inferred_arch": infer_alias_matches(name_lower, ARCH_ALIAS_MAP),
        "inferred_distro": infer_alias_matches(name_lower, DISTRO_ALIAS_MAP),
        "inferred_libc": infer_alias_matches(name_lower, LIBC_ALIAS_MAP),
    }


def asset_matches_platform(
    asset: Mapping[str, Any], requested_platform: Mapping[str, str]
) -> bool:
    for requested_key, inferred_key in (
        ("requested_os", "inferred_os"),
        ("requested_arch", "inferred_arch"),
        ("requested_distro", "inferred_distro"),
        ("requested_libc", "inferred_libc"),
    ):
        requested_value = requested_platform.get(requested_key, "")
        inferred_values = asset.get(inferred_key) or []
        if (
            requested_value
            and inferred_values
            and requested_value not in inferred_values
        ):
            return False
    return True


def prefer_specific_candidates(
    candidates: Sequence[Dict[str, Any]],
    requested_value: str,
    inferred_key: str,
) -> List[Dict[str, Any]]:
    if len(candidates) <= 1 or not requested_value:
        return list(candidates)

    specific_candidates = [
        asset
        for asset in candidates
        if asset.get(inferred_key) and requested_value in asset[inferred_key]
    ]
    return specific_candidates or list(candidates)


def select_candidate_assets(
    repo: str,
    assets: Sequence[Dict[str, Any]],
    params: Mapping[str, Any],
    requested_platform: Mapping[str, str],
) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    asset_url = str(params.get("asset_url") or "")
    asset_name = str(params.get("asset_name") or "")
    asset_name_regex = str(params.get("asset_name_regex") or "")
    asset_name_contains = [
        value.lower()
        for value in ensure_string_list(params.get("asset_name_contains"))
        if value
    ]

    candidates = list(assets)
    selected_family = ""

    if asset_url:
        candidates = [
            asset for asset in assets if asset.get("browser_download_url") == asset_url
        ]
    elif asset_name:
        candidates = [asset for asset in assets if asset.get("name") == asset_name]
    else:
        if asset_name_regex:
            try:
                pattern = re.compile(asset_name_regex)
            except re.error as exc:
                raise ValueError("asset_name_regex is invalid: {0}".format(exc))

            candidates = [
                asset
                for asset in candidates
                if pattern.search(str(asset.get("name") or ""))
            ]

        if asset_name_contains:
            candidates = [
                asset
                for asset in candidates
                if all(
                    token in lower_string(asset.get("name"))
                    for token in asset_name_contains
                )
            ]

        candidates = [
            asset
            for asset in candidates
            if asset_matches_platform(asset, requested_platform)
        ]

        for asset_family in ensure_string_list(params.get("preferred_asset_families")):
            asset_family = asset_family.lower()
            matching_family_assets = [
                asset
                for asset in candidates
                if lower_string(asset.get("asset_family")) == asset_family
            ]
            if matching_family_assets:
                selected_family = asset_family
                candidates = matching_family_assets
                break

        candidates = prefer_specific_candidates(
            candidates,
            requested_platform.get("requested_distro", ""),
            "inferred_distro",
        )
        candidates = prefer_specific_candidates(
            candidates,
            requested_platform.get("requested_libc", ""),
            "inferred_libc",
        )
        candidates = prefer_specific_candidates(
            candidates,
            requested_platform.get("requested_os", ""),
            "inferred_os",
        )
        candidates = prefer_specific_candidates(
            candidates,
            requested_platform.get("requested_arch", ""),
            "inferred_arch",
        )

    if not candidates:
        raise LookupError(
            "No GitHub release assets matched for {0}. Use playbooks/github_releases/inspect-latest.yaml "
            "to inspect normalized assets or provide asset_name, asset_url, asset_name_regex, "
            "or asset_name_contains.".format(repo)
        )

    if len(candidates) != 1:
        candidate_names = ", ".join(
            str(asset.get("name") or "") for asset in candidates
        )
        raise RuntimeError(
            "Multiple GitHub release assets matched for {0}: {1}. Refine selection inputs or inspect "
            "candidates with playbooks/github_releases/inspect-latest.yaml.".format(
                repo,
                candidate_names,
            )
        )

    return candidates, selected_family, candidates[0]


def prepare_download_details(
    params: Mapping[str, Any],
    owner: str,
    name: str,
    release: Mapping[str, Any],
    selected_asset: Mapping[str, Any],
) -> Dict[str, str]:
    explicit_checksum = str(params.get("asset_checksum") or "")
    selected_digest = str(selected_asset.get("digest") or "")
    download_checksum = explicit_checksum or selected_digest

    if explicit_checksum:
        download_verification = "explicit"
    elif selected_digest:
        download_verification = "github-digest"
    else:
        download_verification = "none"

    download_path = os.path.join(
        str(params.get("download_dir") or "/tmp/github-releases"),
        owner,
        name,
        str(release.get("tag_name") or ""),
        str(selected_asset.get("name") or ""),
    )

    return {
        "download_path": download_path,
        "download_checksum": download_checksum,
        "download_verification": download_verification,
    }


def checksum_parts(checksum: str) -> Tuple[str, str]:
    checksum = str(checksum or "").strip()
    if not checksum:
        return "", ""

    if ":" in checksum:
        algorithm, value = checksum.split(":", 1)
        return lower_string(algorithm), value.strip().lower()

    if HEX_DIGEST_PATTERN.match(checksum):
        algorithm = CHECKSUM_LENGTH_TO_ALGORITHM.get(len(checksum), "")
        if algorithm:
            return algorithm, checksum.lower()

    raise ValueError(
        "checksum must be in algorithm:value format or be a recognizable hexadecimal digest"
    )


def file_matches_checksum(path: str, checksum: str) -> bool:
    algorithm, value = checksum_parts(checksum)
    if not algorithm:
        return False

    digest = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == value
