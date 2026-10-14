from __future__ import annotations

import platform
from collections.abc import Mapping, Sequence
from typing import Any

PROC_CPUINFO_PATH = "/proc/cpuinfo"

CPU_FLAG_KEYS = ("flags", "features", "isa", "facilities")

X86_64_ARCHITECTURES = ("x86_64", "amd64")
X86_64_VENDOR_KEY = "vendor_id"
X86_64_MODEL_KEY = "model name"

# Each level requires at least one flag from every group: kernels report the
# same CPUID feature under different names (e.g. Linux displays SSE3 as "pni"
# and LZCNT as "abm", older kernels also reported "osxsave").
X86_64_LEVEL_REQUIREMENTS: dict[str, tuple[tuple[str, ...], ...]] = {
    "x86-64-v2": (
        ("pni", "sse3"),
        ("ssse3",),
        ("sse4_1",),
        ("sse4_2",),
        ("popcnt",),
        ("cx16",),
        ("lahf_lm",),
    ),
    # OSXSAVE is part of the psABI v3 definition but current kernels do not
    # report it in /proc/cpuinfo; they only expose xsave/avx flags once the
    # XSAVE state is OS-enabled, so xsave is the correct proxy here.
    "x86-64-v3": (
        ("avx",),
        ("avx2",),
        ("bmi1",),
        ("bmi2",),
        ("f16c",),
        ("fma",),
        ("movbe",),
        ("abm", "lzcnt"),
        ("xsave", "osxsave"),
    ),
    "x86-64-v4": (
        ("avx512f",),
        ("avx512bw",),
        ("avx512cd",),
        ("avx512dq",),
        ("avx512vl",),
    ),
}

X86_64_LEVEL_ORDER = ("x86-64-v1", "x86-64-v2", "x86-64-v3", "x86-64-v4")


def parse_proc_cpuinfo(path: str = PROC_CPUINFO_PATH) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    entry: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    if entry:
                        entries.append(entry)
                        entry = {}
                    continue

                if ":" not in line:
                    continue

                key, value = line.split(":", 1)
                entry[key.strip().lower()] = value.strip()
    except OSError:
        return []

    if entry:
        entries.append(entry)
    return entries


def detect_cpu_flags(entries: Sequence[Mapping[str, str]]) -> list[str]:
    per_cpu: list[set] = []
    for entry in entries:
        for key in CPU_FLAG_KEYS:
            value = entry.get(key) or ""
            if value:
                per_cpu.append(set(value.split()))
                break

    if not per_cpu:
        return []

    common = per_cpu[0]
    for flags in per_cpu[1:]:
        common &= flags
    return sorted(common)


def compute_x86_64_levels(flags: Sequence[str]) -> dict[str, bool]:
    flag_set = set(flags)
    levels: dict[str, bool] = {}
    supported = bool(flag_set)
    for level in X86_64_LEVEL_ORDER:
        if level != "x86-64-v1":
            supported = supported and all(
                any(feature in flag_set for feature in group) for group in X86_64_LEVEL_REQUIREMENTS[level]
            )
        levels[level] = supported
    return levels


def compute_microarch_levels(architecture: str, flags: Sequence[str]) -> dict[str, bool]:
    if architecture in X86_64_ARCHITECTURES:
        return compute_x86_64_levels(flags)
    return {}


def highest_microarch_level(levels: Mapping[str, bool]) -> str:
    for level in reversed(X86_64_LEVEL_ORDER):
        if levels.get(level):
            return level
    return ""


def collect_cpu_facts() -> dict[str, Any]:
    architecture = platform.machine().lower()
    entries = parse_proc_cpuinfo()
    flags = detect_cpu_flags(entries)
    levels = compute_microarch_levels(architecture, flags)

    first = entries[0] if entries else {}
    vendor = ""
    model = ""
    if architecture in X86_64_ARCHITECTURES:
        vendor = first.get(X86_64_VENDOR_KEY, "")
        model = first.get(X86_64_MODEL_KEY, "")

    return {
        "architecture": architecture,
        "vendor": vendor,
        "model": model,
        "logical_cpus": len(entries),
        "flags": flags,
        "microarch_levels": levels,
        "microarch_level": highest_microarch_level(levels),
    }
