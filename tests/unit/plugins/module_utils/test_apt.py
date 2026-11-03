# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the APT configuration helpers."""

from __future__ import annotations

import pytest
from ansible_collections.ak1ra_lab.general.plugins.module_utils import apt


def test_validate_filename_accepts_debian_style_names() -> None:
    apt.validate_filename("90tailscale", extension=".pref")
    apt.validate_filename("90tailscale.pref", extension=".pref")
    apt.validate_filename("90unattended-upgrades-tailscale", extension=".conf")
    apt.validate_filename("90unattended-upgrades-tailscale.conf", extension=".conf")


@pytest.mark.parametrize("name", ["", ".", "..", "foo/bar", "foo bar", "foo.pref.bak"])
def test_validate_filename_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ValueError):
        apt.validate_filename(name, extension=".pref")


def test_validate_filename_rejects_wrong_extension() -> None:
    with pytest.raises(ValueError, match="no extension or end with '.pref'"):
        apt.validate_filename("90tailscale.conf", extension=".pref")


def test_parse_checksum_with_algorithm_and_bare_digest() -> None:
    assert apt.parse_checksum("sha256:" + "a" * 64) == ("sha256", "a" * 64)
    assert apt.parse_checksum("b" * 64) == ("sha256", "b" * 64)
    assert apt.parse_checksum("") == ("", "")


def test_parse_checksum_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        apt.parse_checksum("sha256:not-hex")
    with pytest.raises(ValueError):
        apt.parse_checksum("sha256:" + "a" * 32)


def test_normalize_preference_release_mapping_uses_short_fields() -> None:
    assert (
        apt.normalize_preference_release({"origin": "Docker", "suite": "trixie", "component": "stable"})
        == "o=Docker,a=trixie,c=stable"
    )


def test_normalize_preference_release_raw_string_is_normalized() -> None:
    assert apt.normalize_preference_release("origin=Docker, archive=trixie") == ("o=Docker,a=trixie")
    assert apt.normalize_preference_release("trixie-backports") == "trixie-backports"


def test_normalize_preference_release_rejects_site_and_duplicates() -> None:
    with pytest.raises(ValueError, match="pin.site"):
        apt.normalize_preference_release({"site": "example.invalid"})
    with pytest.raises(ValueError, match="more than once"):
        apt.normalize_preference_release({"archive": "stable", "a": "stable"})


def test_render_preference_entries() -> None:
    rendered = apt.render_preference_entries(
        [
            {
                "packages": ["linux-*", "initramfs-tools"],
                "pin": {"release": {"codename": "trixie-backports"}},
                "priority": 500,
                "explanation": "Backports are opt-in",
            },
            {
                "packages": "*",
                "pin": {"site": "pkgs.tailscale.com"},
                "priority": 900,
            },
        ]
    )

    assert "Explanation: Backports are opt-in" in rendered
    assert "Package: linux-* initramfs-tools" in rendered
    assert "Pin: release n=trixie-backports" in rendered
    assert "Pin-Priority: 500" in rendered
    assert "Package: *" in rendered
    assert "Pin: origin pkgs.tailscale.com" in rendered
    assert "Pin-Priority: 900" in rendered


def test_render_preference_entries_rejects_zero_priority() -> None:
    with pytest.raises(ValueError, match="must not be 0"):
        apt.render_preference_entries([{"packages": "*", "pin": {"release": "stable"}, "priority": 0}])


def test_normalize_origins_pattern_full_names() -> None:
    assert (
        apt.normalize_origins_pattern({"o": "Docker", "suite": "trixie", "component": "stable"})
        == "origin=Docker,archive=trixie,component=stable"
    )
    assert (
        apt.normalize_origins_pattern("origin=Debian,codename=${distro_codename},label=Debian")
        == "origin=Debian,codename=${distro_codename},label=Debian"
    )


def test_normalize_origins_pattern_allows_escaped_comma() -> None:
    assert apt.normalize_origins_pattern({"label": r"Debian\,Archive"}) == (r"label=Debian\,Archive")


def test_normalize_origins_pattern_rejects_unknown_fields_and_duplicates() -> None:
    with pytest.raises(ValueError, match="unknown origins pattern field"):
        apt.normalize_origins_pattern({"version": "13"})
    with pytest.raises(ValueError, match="more than once"):
        apt.normalize_origins_pattern({"archive": "stable", "a": "stable"})


def test_format_apt_conf_value_and_periodic_value() -> None:
    assert apt.format_apt_conf_value(True, "automatic_reboot") == "true"
    assert apt.format_apt_conf_value(False, "automatic_reboot") == "false"
    assert apt.format_apt_conf_value(2, "count") == "2"
    assert apt.format_periodic_value(True, "periodic") == "1"
    assert apt.format_periodic_value(7, "periodic") == "7"
    assert apt.format_periodic_value("7", "periodic") == "7"
    with pytest.raises(ValueError):
        apt.format_periodic_value("daily", "periodic")


def test_render_apt_conf_option_accepts_generic_names() -> None:
    assert apt.render_apt_conf_option("Acquire::ForceIPv4", True) == 'Acquire::ForceIPv4 "true";'


def test_render_apt_conf_options_scalars_and_lists() -> None:
    rendered = apt.render_apt_conf_options(
        {
            "Acquire::http::Proxy": "http://proxy.example:3128",
            "Acquire::ForceIPv4": True,
            "Unattended-Upgrade::Origins-Pattern": [
                "origin=Debian,codename=trixie",
                "origin=Debian,codename=trixie-security",
            ],
        },
        header="Managed by test",
    )

    assert rendered.startswith("// Managed by test\n\n")
    assert 'Acquire::http::Proxy "http://proxy.example:3128";' in rendered
    assert 'Acquire::ForceIPv4 "true";' in rendered
    assert 'Unattended-Upgrade::Origins-Pattern:: "origin=Debian,codename=trixie";' in rendered
    assert 'Unattended-Upgrade::Origins-Pattern:: "origin=Debian,codename=trixie-security";' in rendered


def test_render_apt_conf_options_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one APT configuration option"):
        apt.render_apt_conf_options({})
    with pytest.raises(ValueError, match="at least one APT configuration option"):
        apt.render_apt_conf_options({"Acquire::http::Proxy": []})


def test_render_apt_conf_options_rejects_invalid_names_and_values() -> None:
    with pytest.raises(ValueError, match="invalid APT configuration option name"):
        apt.render_apt_conf_options({"Bad Name": "value"})
    with pytest.raises(ValueError):
        apt.render_apt_conf_options({"Acquire::http::Proxy": None})


def test_data_checksum_and_armored_detection() -> None:
    assert apt.data_checksum(b"abc") == ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    assert apt.is_armored_key(b"-----BEGIN PGP PUBLIC KEY BLOCK-----\n")
    assert not apt.is_armored_key(b"\x99\x02\x0d\x04")
