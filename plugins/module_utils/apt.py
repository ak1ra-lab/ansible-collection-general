# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Shared helpers for the APT configuration modules.

The helpers in this module are intentionally independent from an
``AnsibleModule`` wherever possible.  The rendering functions are pure and
unit-tested directly; the small file/download helpers accept an
``AnsibleModule`` so every module reports failures and check-mode changes in
the same way.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import posixpath
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from typing import Any

from ansible.module_utils.urls import fetch_url

PREFERENCES_DIR = "/etc/apt/preferences.d"
APT_CONF_DIR = "/etc/apt/apt.conf.d"
KEYRINGS_DIR = "/etc/apt/keyrings"
SHARE_KEYRINGS_DIR = "/usr/share/keyrings"

_APT_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_APT_CONF_OPTION_RE = re.compile(r"^[A-Za-z0-9/_:.+-]+$")
_APT_CONF_OPTION_PREFIXES = ("Unattended-Upgrade::", "APT::Periodic::")

# APT's apt_preferences(5) parser only understands these single-letter
# prefixes.  A full name such as ``origin=`` is silently ignored by APT (and
# can even turn into a match-all record for files without a Release file), so
# the public API accepts full names and normalizes them to the short form.
PREFERENCE_RELEASE_ALIASES: dict[str, str] = {
    "a": "a",
    "archive": "a",
    "suite": "a",
    "c": "c",
    "component": "c",
    "l": "l",
    "label": "l",
    "n": "n",
    "codename": "n",
    "o": "o",
    "origin": "o",
    "v": "v",
    "version": "v",
    "b": "b",
    "arch": "b",
    "architecture": "b",
}

# unattended-upgrades accepts full names and abbreviations.  Emitting the
# full names keeps the generated file readable; the module normalizes any
# accepted alias to these keys.
UNATTENDED_ORIGIN_ALIASES: dict[str, str] = {
    "a": "archive",
    "archive": "archive",
    "suite": "archive",
    "c": "component",
    "component": "component",
    "l": "label",
    "label": "label",
    "n": "codename",
    "codename": "codename",
    "o": "origin",
    "origin": "origin",
    "site": "site",
}

UNATTENDED_BOOL_OPTIONS: dict[str, str] = {
    "auto_fix_interrupted_dpkg": "Unattended-Upgrade::AutoFixInterruptedDpkg",
    "automatic_reboot": "Unattended-Upgrade::Automatic-Reboot",
    "automatic_reboot_with_users": "Unattended-Upgrade::Automatic-Reboot-WithUsers",
    "install_on_shutdown": "Unattended-Upgrade::InstallOnShutdown",
    "minimal_steps": "Unattended-Upgrade::MinimalSteps",
    "remove_new_unused_dependencies": "Unattended-Upgrade::Remove-New-Unused-Dependencies",
    "remove_unused_dependencies": "Unattended-Upgrade::Remove-Unused-Dependencies",
    "remove_unused_kernel_packages": "Unattended-Upgrade::Remove-Unused-Kernel-Packages",
    "syslog_enable": "Unattended-Upgrade::SyslogEnable",
    "verbose": "Unattended-Upgrade::Verbose",
}

UNATTENDED_STRING_OPTIONS: dict[str, str] = {
    "automatic_reboot_time": "Unattended-Upgrade::Automatic-Reboot-Time",
    "mail": "Unattended-Upgrade::Mail",
    "mail_report": "Unattended-Upgrade::MailReport",
}

PERIODIC_OPTIONS: dict[str, str] = {
    "autoclean_interval": "APT::Periodic::AutocleanInterval",
    "clean_interval": "APT::Periodic::CleanInterval",
    "download_upgradeable_packages": "APT::Periodic::Download-Upgradeable-Packages",
    "unattended_upgrade": "APT::Periodic::Unattended-Upgrade",
    "update_package_lists": "APT::Periodic::Update-Package-Lists",
}

MAIL_REPORT_CHOICES = ("always", "only-on-error", "on-change")


def validate_filename(name: str, *, extension: str) -> None:
    """Validate a basename accepted by APT's configuration directories."""

    if not name or name in {".", ".."}:
        raise ValueError("file name must not be empty")
    if "/" in name or "\\" in name:
        raise ValueError(f"file name {name!r} must be a basename without path separators")
    if not _APT_FILENAME_RE.fullmatch(name):
        raise ValueError(f"file name {name!r} may only contain letters, digits, hyphen, underscore, and period")
    if "." in name and not name.endswith(extension):
        raise ValueError(f"file name {name!r} must have no extension or end with {extension!r}")


def _ensure_text(value: Any, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{field} must be a string")  # noqa: TRY004
    text = str(value).strip()
    if "\n" in text or "\r" in text:
        raise ValueError(f"{field} must not contain a newline")
    return text


def _ensure_non_empty(value: Any, field: str) -> str:
    text = _ensure_text(value, field)
    if not text:
        raise ValueError(f"{field} must not be empty")
    return text


def parse_checksum(checksum: str) -> tuple[str, str]:
    """Return ``(algorithm, hexdigest)`` for an Ansible-style checksum."""

    value = checksum.strip()
    if not value:
        return "", ""

    if ":" in value:
        algorithm, digest = value.split(":", 1)
        algorithm = algorithm.lower()
    else:
        algorithm = {
            32: "md5",
            40: "sha1",
            56: "sha224",
            64: "sha256",
            96: "sha384",
            128: "sha512",
        }.get(len(value), "")
        digest = value

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"unsupported checksum algorithm {algorithm!r}")
    digest = digest.strip().lower()
    if not re.fullmatch(r"[0-9a-f]+", digest):
        raise ValueError("checksum digest must be hexadecimal")
    expected_length = hashlib.new(algorithm).digest_size * 2
    if len(digest) != expected_length:
        raise ValueError(f"{algorithm} checksum must contain {expected_length} hexadecimal characters")
    return algorithm, digest


def data_checksum(data: bytes, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    digest.update(data)
    return digest.hexdigest()


def normalize_preference_release(release: str | Mapping[str, Any]) -> str:
    """Normalize a ``Pin: release`` value to APT's short field names."""

    if isinstance(release, str):
        value = release.strip()
        if not value:
            raise ValueError("pin.release must not be empty")
        if "=" not in value:
            if "\n" in value or "\r" in value:
                raise ValueError("pin.release must not contain a newline")
            return value
        tokens = [token.strip() for token in value.split(",") if token.strip()]
        return _normalize_release_tokens(tokens)

    if not isinstance(release, Mapping):
        raise ValueError("pin.release must be a mapping or a string")  # noqa: TRY004

    tokens = []
    for key, raw_value in release.items():
        key_text = _ensure_non_empty(key, "pin.release field")
        tokens.append(f"{key_text}={_ensure_text(raw_value, f'pin.release.{key_text}')}")
    return _normalize_release_tokens(tokens)


def _normalize_release_tokens(tokens: Sequence[str]) -> str:
    seen: set[str] = set()
    normalized: list[str] = []

    for token in tokens:
        if "=" not in token:
            raise ValueError(
                "pin.release entries must use field=value form; use a plain string only "
                "for a single archive, codename, or version"
            )
        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"invalid pin.release entry {token!r}")

        if key in {"site"}:
            raise ValueError("pin.release does not support 'site'; use pin.site to generate 'Pin: origin <hostname>'")
        try:
            short_key = PREFERENCE_RELEASE_ALIASES[key]
        except KeyError as exc:
            allowed = ", ".join(sorted(PREFERENCE_RELEASE_ALIASES))
            raise ValueError(f"unknown pin.release field {key!r}; accepted fields are: {allowed}") from exc

        if short_key in seen:
            raise ValueError(f"pin.release field {key!r} is set more than once")
        if "," in value:
            raise ValueError(f"pin.release field {key!r} must not contain a comma")
        if '"' in value:
            raise ValueError(f"pin.release field {key!r} must not contain a double quote")
        seen.add(short_key)
        normalized.append(f"{short_key}={value}")

    if not normalized:
        raise ValueError("pin.release must contain at least one field")
    return ",".join(normalized)


def normalize_pin_site(site: Any) -> str:
    value = _ensure_text(site, "pin.site")
    if any(character.isspace() for character in value):
        raise ValueError("pin.site must not contain whitespace")
    if '"' in value:
        raise ValueError("pin.site must not contain a double quote")
    return value


def normalize_pin_version(version: Any) -> str:
    value = _ensure_non_empty(version, "pin.version")
    if any(character.isspace() for character in value):
        raise ValueError("pin.version must not contain whitespace")
    if '"' in value:
        raise ValueError("pin.version must not contain a double quote")
    return value


def format_packages(packages: Any) -> str:
    if isinstance(packages, str):
        value = _ensure_non_empty(packages, "packages")
        return value
    if isinstance(packages, Sequence) and not isinstance(packages, (bytes, bytearray)):
        items = [_ensure_non_empty(item, "packages item") for item in packages]
        if not items:
            raise ValueError("packages must contain at least one package pattern")
        return " ".join(items)
    raise ValueError("packages must be a string or a list of strings")


def format_explanation(explanation: Any) -> list[str]:
    if explanation is None or explanation == "":
        return []
    if isinstance(explanation, str):
        lines = explanation.splitlines()
    elif isinstance(explanation, Sequence) and not isinstance(explanation, (bytes, bytearray)):
        lines = []
        for item in explanation:
            lines.extend(_ensure_text(item, "explanation item").splitlines())
    else:
        raise ValueError("explanation must be a string or a list of strings")  # noqa: TRY004
    return [f"Explanation: {line.strip()}" for line in lines if line.strip()]


def render_preference_entries(entries: Sequence[Mapping[str, Any]]) -> str:
    """Render apt_preferences(5) records."""

    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes, bytearray)):
        raise ValueError("entries must be a list of mappings")  # noqa: TRY004
    if not entries:
        raise ValueError("entries must contain at least one preference record")

    blocks: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise ValueError(f"entries[{index}] must be a mapping")  # noqa: TRY004

        packages = format_packages(entry.get("packages"))
        priority = entry.get("priority")
        if priority is None:
            raise ValueError(f"entries[{index}].priority is required")
        if isinstance(priority, bool) or not isinstance(priority, (int, str)):
            raise ValueError(f"entries[{index}].priority must be an integer")  # noqa: TRY004
        try:
            priority_value = int(priority)
        except (TypeError, ValueError):
            raise ValueError(f"entries[{index}].priority must be an integer")
        if priority_value == 0:
            raise ValueError(f"entries[{index}].priority must not be 0")

        pin = entry.get("pin")
        if not isinstance(pin, Mapping):
            raise ValueError(f"entries[{index}].pin must be a mapping")  # noqa: TRY004
        pin_keys = set(pin)
        if len(pin_keys) != 1:
            raise ValueError(f"entries[{index}].pin must contain exactly one of release, site, or version")
        pin_type = next(iter(pin_keys))
        if pin_type == "release":
            pin_line = f"release {normalize_preference_release(pin['release'])}"
        elif pin_type == "site":
            site = normalize_pin_site(pin["site"])
            pin_line = f'origin "{site}"' if site == "" else f"origin {site}"
        elif pin_type == "version":
            pin_line = f"version {normalize_pin_version(pin['version'])}"
        else:
            raise ValueError(f"entries[{index}].pin has unknown key {pin_type!r}; use release, site, or version")

        lines = format_explanation(entry.get("explanation"))
        lines.append(f"Package: {packages}")
        lines.append(f"Pin: {pin_line}")
        lines.append(f"Pin-Priority: {priority_value}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks) + "\n"


def _split_origins_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    escaped = False
    for character in value:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            current.append(character)
            escaped = True
        elif character == ",":
            tokens.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    tokens.append("".join(current).strip())
    return [token for token in tokens if token]


def _normalize_origins_tokens(tokens: Sequence[str]) -> str:
    seen: set[str] = set()
    normalized: list[str] = []
    for token in tokens:
        if "=" not in token:
            raise ValueError(
                "origins pattern entries must use field=value form, for example origin=Debian,codename=trixie"
            )
        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"invalid origins pattern entry {token!r}")
        try:
            canonical = UNATTENDED_ORIGIN_ALIASES[key]
        except KeyError as exc:
            allowed = ", ".join(sorted(UNATTENDED_ORIGIN_ALIASES))
            raise ValueError(f"unknown origins pattern field {key!r}; accepted fields are: {allowed}") from exc
        if canonical in seen:
            raise ValueError(f"origins pattern field {key!r} is set more than once")
        _validate_origins_value(value, key)
        seen.add(canonical)
        normalized.append(f"{canonical}={value}")
    if not normalized:
        raise ValueError("origins patterns must contain at least one field")
    return ",".join(normalized)


def _validate_origins_value(value: str, key: str) -> None:
    if "\n" in value or "\r" in value:
        raise ValueError(f"origins pattern field {key!r} must not contain a newline")
    if '"' in value:
        raise ValueError(f"origins pattern field {key!r} must not contain a double quote")
    if "=" in value:
        raise ValueError(f"origins pattern field {key!r} must not contain '='")
    if "," in value.replace("\\,", ""):
        raise ValueError(f"origins pattern field {key!r} must not contain an unescaped comma")


def normalize_origins_pattern(pattern: str | Mapping[str, Any]) -> str:
    if isinstance(pattern, str):
        value = pattern.strip()
        if not value:
            raise ValueError("origins pattern must not be empty")
        return _normalize_origins_tokens(_split_origins_tokens(value))
    if not isinstance(pattern, Mapping):
        raise ValueError("origins pattern must be a mapping or a string")  # noqa: TRY004

    tokens = []
    for key, raw_value in pattern.items():
        key_text = _ensure_non_empty(key, "origins pattern field")
        tokens.append(f"{key_text}={_ensure_text(raw_value, f'origins_patterns.{key_text}')}")
    return _normalize_origins_tokens(tokens)


def format_apt_conf_value(value: Any, field: str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        if "\n" in text or "\r" in text:
            raise ValueError(f"{field} must not contain a newline")
        if '"' in text:
            raise ValueError(f"{field} must not contain a double quote")
        return text
    raise ValueError(f"{field} must be a string, integer, or boolean")


def format_periodic_value(value: Any, field: str) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{field} must not be negative")
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        if not text or not text.isdigit():
            raise ValueError(f"{field} must be a non-negative integer")
        return text
    raise ValueError(f"{field} must be a non-negative integer")


def render_apt_conf_option(name: str, value: Any) -> str:
    if not _APT_CONF_OPTION_RE.fullmatch(name):
        raise ValueError(f"invalid APT configuration option name {name!r}")
    if not name.startswith(_APT_CONF_OPTION_PREFIXES):
        raise ValueError(f"APT configuration option {name!r} must start with " + " or ".join(_APT_CONF_OPTION_PREFIXES))
    return f'{name} "{format_apt_conf_value(value, name)}";'


def validate_apt_conf(module: Any, content: str) -> None:
    """Validate generated apt.conf syntax with apt-config(8)."""

    apt_config = module.get_bin_path("apt-config", required=True)
    fd, path = tempfile.mkstemp(dir=module.tmpdir, suffix=".conf")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        rc, stdout, stderr = module.run_command([apt_config, "-c", path, "dump"])
        if rc != 0:
            detail = (stderr or stdout).strip()
            module.fail_json(
                msg=f"generated APT configuration is invalid: {detail}",
                stdout=stdout,
                stderr=stderr,
                rc=rc,
            )
    finally:
        os.unlink(path)


def ensure_directory(module: Any, path: str, mode: str = "0755") -> bool:
    if os.path.isdir(path):
        return False
    if os.path.exists(path):
        module.fail_json(msg=f"{path} exists and is not a directory")
    if module.check_mode:
        return True
    try:
        os.makedirs(path, mode=int(mode, 8))
    except OSError as exc:
        module.fail_json(msg=f"failed to create directory {path}: {exc}")
    file_args = module.load_file_common_arguments({"path": path, "mode": mode, "owner": "root", "group": "root"})
    module.set_directory_attributes_if_different(file_args, False)
    return True


def _file_attributes(module: Any, path: str, mode: str, owner: str, group: str) -> bool:
    file_args = module.load_file_common_arguments({"path": path, "mode": mode, "owner": owner, "group": group})
    return bool(module.set_fs_attributes_if_different(file_args, False))


def write_file(
    module: Any,
    path: str,
    data: bytes,
    mode: str = "0644",
    owner: str = "root",
    group: str = "root",
) -> bool:
    """Write bytes atomically and apply file attributes."""

    parent = os.path.dirname(path) or "."
    changed = ensure_directory(module, parent)

    existing = read_file(module, path)
    if existing != data:
        changed = True
        if not module.check_mode:
            fd, temp_path = tempfile.mkstemp(dir=module.tmpdir)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(data)
                module.atomic_move(temp_path, path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    if os.path.exists(path) or not module.check_mode:
        changed |= _file_attributes(module, path, mode, owner, group)
    return changed


def remove_file(module: Any, path: str) -> bool:
    if not os.path.exists(path):
        return False
    if not module.check_mode:
        try:
            os.unlink(path)
        except FileNotFoundError:
            return False
        except OSError as exc:
            module.fail_json(msg=f"failed to remove {path}: {exc}")
    return True


def read_file(module: Any, path: str) -> bytes | None:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except FileNotFoundError:
        return None
    except OSError as exc:
        module.fail_json(msg=f"failed to read {path}: {exc}")
    return None


def download_bytes(module: Any, url: str, *, timeout: int) -> bytes:
    response, info = fetch_url(module, url, timeout=timeout)
    if info["status"] != 200:
        module.fail_json(msg=f"failed to download {url}: {info.get('msg', info['status'])}")
    try:
        data = response.read()
    finally:
        response.close()
    if not data:
        module.fail_json(msg=f"downloaded file from {url} is empty")
    return data


def verify_checksum(module: Any, data: bytes, checksum: str, source: str) -> None:
    if not checksum:
        return
    try:
        algorithm, expected = parse_checksum(checksum)
    except ValueError as exc:
        module.fail_json(msg=f"invalid checksum for {source}: {exc}")
    actual = data_checksum(data, algorithm)
    if actual != expected:
        module.fail_json(
            msg=f"checksum mismatch for {source}: expected {algorithm}:{expected}, got {algorithm}:{actual}"
        )


def decode_keyring_content(
    module: Any,
    *,
    content: str = "",
    content_base64: str = "",
) -> bytes:
    if content and content_base64:
        module.fail_json(msg="content and content_base64 are mutually exclusive")
    if content_base64:
        try:
            data = base64.b64decode("".join(content_base64.split()), validate=True)
        except (binascii.Error, ValueError) as exc:
            module.fail_json(msg=f"content_base64 is not valid base64: {exc}")
    else:
        data = content.encode("utf-8")
    if not data:
        module.fail_json(msg="keyring content is empty")
    return data


def extract_deb_member(module: Any, deb_path: str, member: str) -> bytes:
    """Extract one regular file from a .deb without installing the package."""

    normalized = posixpath.normpath(member.lstrip("/"))
    if normalized in {"", "."} or normalized.startswith(".."):
        module.fail_json(msg=f"invalid .deb member path {member!r}")

    dpkg_deb = module.get_bin_path("dpkg-deb", required=True)
    temporary_directory = tempfile.mkdtemp(dir=module.tmpdir)
    try:
        rc, stdout, stderr = module.run_command([dpkg_deb, "-x", deb_path, temporary_directory])
        if rc != 0:
            module.fail_json(
                msg=f"failed to extract {deb_path}: {(stderr or stdout).strip()}",
                stdout=stdout,
                stderr=stderr,
                rc=rc,
            )
        candidate = os.path.join(temporary_directory, normalized)
        real_root = os.path.realpath(temporary_directory)
        real_candidate = os.path.realpath(candidate)
        if os.path.commonpath([real_root, real_candidate]) != real_root:
            module.fail_json(msg=f".deb member {member!r} escapes the package root")
        if os.path.islink(candidate) or not os.path.isfile(candidate):
            module.fail_json(msg=f".deb member {member!r} is not a regular file")
        try:
            with open(candidate, "rb") as handle:
                return handle.read()
        except OSError as exc:
            module.fail_json(msg=f"failed to read .deb member {member!r}: {exc}")
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)

    module.fail_json(msg=f"failed to extract .deb member {member!r}")
    return b""


def is_armored_key(data: bytes) -> bool:
    return b"-----BEGIN PGP PUBLIC KEY BLOCK-----" in data
