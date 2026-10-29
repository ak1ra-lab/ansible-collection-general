# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the cpu_info module_utils.

The parsers are pure functions over /proc/cpuinfo-shaped mappings; only
collect_cpu_facts() touches the host, so it is tested with both platform and
the parser patched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from ansible_collections.ak1ra_lab.general.plugins.module_utils import cpu

CPUINFO = """\
processor\t: 0
vendor_id\t: AuthenticAMD
model name\t: AMD EPYC 7B13
flags\t\t: fpu pni ssse3 sse4_1 sse4_2 popcnt cx16 lahf_lm avx avx2 bmi1 bmi2 f16c fma movbe abm xsave
\n\
processor\t: 1
vendor_id\t: AuthenticAMD
model name\t: AMD EPYC 7B13
flags\t\t: fpu pni ssse3 sse4_1 sse4_2 popcnt cx16 lahf_lm avx avx2 bmi1 bmi2 f16c fma movbe abm xsave
"""


def test_parse_proc_cpuinfo_reads_entries(tmp_path: Path) -> None:
    path = tmp_path / "cpuinfo"
    path.write_text(CPUINFO, encoding="utf-8")

    entries = cpu.parse_proc_cpuinfo(str(path))

    assert len(entries) == 2
    assert entries[0]["vendor_id"] == "AuthenticAMD"
    assert entries[0]["model name"] == "AMD EPYC 7B13"
    assert "avx2" in entries[1]["flags"]


def test_parse_proc_cpuinfo_missing_file_returns_empty() -> None:
    assert cpu.parse_proc_cpuinfo("/nonexistent/cpuinfo") == []


def test_detect_cpu_flags_intersects_logical_cpus() -> None:
    entries = [
        {"flags": "sse4_1 avx avx2"},
        {"flags": "sse4_1 avx"},
    ]

    assert cpu.detect_cpu_flags(entries) == ["avx", "sse4_1"]


def test_detect_cpu_flags_uses_architecture_specific_key() -> None:
    entries = [{"features": "fp asimd"}, {"features": "fp asimd"}]

    assert cpu.detect_cpu_flags(entries) == ["asimd", "fp"]


def test_compute_x86_64_levels_stops_at_missing_requirement() -> None:
    v2_flags = ["pni", "ssse3", "sse4_1", "sse4_2", "popcnt", "cx16", "lahf_lm"]

    levels = cpu.compute_x86_64_levels(v2_flags)

    assert levels == {
        "x86-64-v1": True,
        "x86-64-v2": True,
        "x86-64-v3": False,
        "x86-64-v4": False,
    }


def test_compute_x86_64_levels_empty_flags_are_unsupported() -> None:
    assert cpu.compute_x86_64_levels([]) == {
        "x86-64-v1": False,
        "x86-64-v2": False,
        "x86-64-v3": False,
        "x86-64-v4": False,
    }


def test_compute_microarch_levels_ignores_non_x86() -> None:
    assert cpu.compute_microarch_levels("aarch64", ["asimd"]) == {}


def test_highest_microarch_level() -> None:
    levels = {"x86-64-v1": True, "x86-64-v2": True, "x86-64-v3": True, "x86-64-v4": False}

    assert cpu.highest_microarch_level(levels) == "x86-64-v3"
    assert cpu.highest_microarch_level({}) == ""


def test_collect_cpu_facts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "cpuinfo"
    path.write_text(CPUINFO, encoding="utf-8")
    entries = cpu.parse_proc_cpuinfo(str(path))
    monkeypatch.setattr(cpu.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(cpu, "parse_proc_cpuinfo", lambda: entries)

    facts = cpu.collect_cpu_facts()

    assert facts["architecture"] == "x86_64"
    assert facts["vendor"] == "AuthenticAMD"
    assert facts["model"] == "AMD EPYC 7B13"
    assert facts["logical_cpus"] == 2
    assert facts["microarch_level"] == "x86-64-v3"
    assert "avx2" in facts["flags"]
