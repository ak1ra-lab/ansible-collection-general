# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: apt_unattended_upgrades
short_description: Manage unattended-upgrades policy snippets
description:
  - Render an APT configuration drop-in for unattended-upgrades.
  - The module can add origins patterns, package blacklists and whitelists,
    automatic reboot settings, and the C(APT::Periodic) schedule options.
  - Origins patterns accept both the full names used by unattended-upgrades
    (C(origin), C(archive), C(codename), C(component), C(label), C(site)) and
    the single-letter aliases. Generated files use the full names.
options:
  name:
    description:
      - Basename of the file in C(/etc/apt/apt.conf.d).
      - Mutually exclusive with O(path).
    type: str
  path:
    description:
      - Full path of the configuration file.
      - Mutually exclusive with O(name).
    type: path
  state:
    description:
      - Whether the configuration file should exist.
    type: str
    choices: [present, absent]
    default: present
  origins_patterns:
    description:
      - Origins patterns appended to C(Unattended-Upgrade::Origins-Pattern).
      - Each item is either a mapping of pattern fields or a raw
        C(field=value,field=value) string.
      - Supported fields are C(origin)/C(o), C(archive)/C(suite)/C(a),
        C(codename)/C(n), C(component)/C(c), C(label)/C(l), and C(site).
    type: list
    elements: raw
    default: []
  package_blacklist:
    description:
      - Python regular expressions for packages that unattended-upgrades must
        not upgrade.
    type: list
    elements: str
    default: []
  package_whitelist:
    description:
      - Python regular expressions for packages that unattended-upgrades may
        upgrade.
    type: list
    elements: str
    default: []
  package_whitelist_strict:
    description:
      - Whether only whitelisted packages may be upgraded.
    type: bool
  automatic_reboot:
    description:
      - Reboot automatically when C(/var/run/reboot-required) exists after an
        upgrade.
    type: bool
  automatic_reboot_with_users:
    description:
      - Allow automatic reboots while users are logged in.
    type: bool
  automatic_reboot_time:
    description:
      - Reboot time as C(HH:MM) or C(now), used with O(automatic_reboot).
    type: str
    default: ''
  mail:
    description:
      - Mail address for upgrade reports.
    type: str
    default: ''
  mail_report:
    description:
      - When to send the upgrade report.
    type: str
    choices: [always, only-on-error, on-change]
  remove_unused_dependencies:
    description:
      - Run an C(apt-get autoremove)-style cleanup after upgrades.
    type: bool
  remove_new_unused_dependencies:
    description:
      - Remove dependencies that became unused during the upgrade.
    type: bool
  remove_unused_kernel_packages:
    description:
      - Remove unused kernel-related packages.
    type: bool
  minimal_steps:
    description:
      - Install upgrades in small steps so an interrupted run can stop safely.
    type: bool
  install_on_shutdown:
    description:
      - Install pending upgrades during shutdown instead of while running.
    type: bool
  auto_fix_interrupted_dpkg:
    description:
      - Run C(dpkg --force-confold --configure -a) after an unclean dpkg exit.
    type: bool
  syslog_enable:
    description:
      - Enable syslog logging from unattended-upgrades.
    type: bool
  verbose:
    description:
      - Enable verbose unattended-upgrades logging.
    type: bool
  periodic:
    description:
      - C(APT::Periodic) schedule values.
      - Supported keys are C(update_package_lists),
        C(unattended_upgrade), C(download_upgradeable_packages),
        C(autoclean_interval), and C(clean_interval).
    type: dict
    default: {}
  validate:
    description:
      - Validate the generated file with C(apt-config -c FILE dump) before
        writing it.
    type: bool
    default: true
  mode:
    description:
      - File mode of the configuration file.
    type: raw
    default: '0644'
  owner:
    description:
      - Owner of the configuration file.
    type: str
    default: root
  group:
    description:
      - Group of the configuration file.
    type: str
    default: root
notes:
  - APT parses files in C(/etc/apt/apt.conf.d) in alphanumeric order. A later
    scalar option overrides an earlier one; list options are appended with
    C(::) entries.
  - Debian and Ubuntu ship different default policy files, but both accept
    C(Unattended-Upgrade::Origins-Pattern); Ubuntu's legacy
    C(Allowed-Origins) entries remain additive.
author:
  - ak1ra (@ak1ra-lab)
"""

EXAMPLES = r"""
- name: Add a vendor repository to unattended-upgrades
  ak1ra_lab.general.apt_unattended_upgrades:
    name: example
    origins_patterns:
      - site: packages.example.invalid

- name: Enable automatic reboots and the daily periodic schedule
  ak1ra_lab.general.apt_unattended_upgrades:
    name: debian-base
    origins_patterns:
      - origin: Debian
        codename: trixie
        label: Debian
    automatic_reboot: true
    automatic_reboot_time: "02:00"
    periodic:
      update_package_lists: 1
      unattended_upgrade: 1

- name: Remove the role-owned policy snippet
  ak1ra_lab.general.apt_unattended_upgrades:
    name: example
    state: absent
"""

RETURN = r"""
path:
  description: Path of the managed configuration file.
  returned: always
  type: str
  sample: /etc/apt/apt.conf.d/90unattended-upgrades-example
changed:
  description: Whether the configuration file changed.
  returned: always
  type: bool
"""

import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ak1ra_lab.general.plugins.module_utils.apt import (
    APT_CONF_DIR,
    MAIL_REPORT_CHOICES,
    PERIODIC_OPTIONS,
    UNATTENDED_BOOL_OPTIONS,
    UNATTENDED_STRING_OPTIONS,
    format_apt_conf_value,
    format_periodic_value,
    normalize_origins_pattern,
    remove_file,
    render_apt_conf_option,
    validate_apt_conf,
    validate_filename,
    write_file,
)

_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _resolve_path(module: AnsibleModule) -> str:
    name = module.params["name"]
    path = module.params["path"]
    if not name and not path:
        module.fail_json(msg="one of name or path is required")

    if name:
        try:
            validate_filename(name, extension=".conf")
        except ValueError as exc:
            module.fail_json(msg=str(exc))
        return os.path.join(APT_CONF_DIR, name)

    if not os.path.isabs(path):
        module.fail_json(msg="path must be an absolute path")
    try:
        validate_filename(os.path.basename(path), extension=".conf")
    except ValueError as exc:
        module.fail_json(msg=str(exc))
    return path


def _validate_regex(value: str, field: str) -> str:
    text = format_apt_conf_value(value, field)
    try:
        re.compile(text)
    except re.error as exc:
        raise ValueError(f"{field} is not a valid Python regular expression: {exc}") from exc
    return text


def _append_list_option(lines: list[str], option: str, values: list[str]) -> None:
    for value in values:
        lines.append(f'{option}:: "{value}";')


def _render(module: AnsibleModule) -> str:
    params = module.params
    lines = [
        "// Managed by Ansible (ak1ra_lab.general.apt_unattended_upgrades).",
        "",
    ]
    populated = False

    for index, pattern in enumerate(params["origins_patterns"] or []):
        try:
            normalized = normalize_origins_pattern(pattern)
        except ValueError as exc:
            module.fail_json(msg=f"origins_patterns[{index}]: {exc}")
        lines.append(f'Unattended-Upgrade::Origins-Pattern:: "{normalized}";')
        populated = True

    for field in ("package_blacklist", "package_whitelist"):
        option = (
            "Unattended-Upgrade::Package-Blacklist"
            if field == "package_blacklist"
            else "Unattended-Upgrade::Package-Whitelist"
        )
        values = []
        for index, value in enumerate(params[field] or []):
            try:
                values.append(_validate_regex(value, f"{field}[{index}]"))
            except ValueError as exc:
                module.fail_json(msg=str(exc))
        if values:
            _append_list_option(lines, option, values)
            populated = True

    for field, option in UNATTENDED_BOOL_OPTIONS.items():
        value = params[field]
        if value is not None:
            lines.append(render_apt_conf_option(option, value))
            populated = True

    if params["package_whitelist_strict"] is not None:
        lines.append(
            render_apt_conf_option(
                "Unattended-Upgrade::Package-Whitelist-Strict",
                params["package_whitelist_strict"],
            )
        )
        populated = True

    for field, option in UNATTENDED_STRING_OPTIONS.items():
        value = params[field]
        if not value:
            continue
        if field == "automatic_reboot_time" and value != "now" and not _TIME_RE.fullmatch(value):
            module.fail_json(msg="automatic_reboot_time must be 'now' or a 24-hour HH:MM value")
        lines.append(render_apt_conf_option(option, value))
        populated = True

    for key, value in (params["periodic"] or {}).items():
        if key not in PERIODIC_OPTIONS:
            module.fail_json(
                msg=f"unknown periodic key {key!r}; accepted keys are: " + ", ".join(sorted(PERIODIC_OPTIONS))
            )
        try:
            rendered = format_periodic_value(value, f"periodic.{key}")
        except ValueError as exc:
            module.fail_json(msg=str(exc))
        lines.append(f'{PERIODIC_OPTIONS[key]} "{rendered}";')
        populated = True

    if not populated:
        module.fail_json(
            msg="at least one origins pattern, package rule, unattended-upgrades option, "
            "or periodic option must be set when state=present"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "name": {"type": "str"},
            "path": {"type": "path"},
            "state": {
                "type": "str",
                "choices": ["present", "absent"],
                "default": "present",
            },
            "origins_patterns": {"type": "list", "elements": "raw", "default": []},
            "package_blacklist": {"type": "list", "elements": "str", "default": []},
            "package_whitelist": {"type": "list", "elements": "str", "default": []},
            "package_whitelist_strict": {"type": "bool"},
            "automatic_reboot": {"type": "bool"},
            "automatic_reboot_with_users": {"type": "bool"},
            "automatic_reboot_time": {"type": "str", "default": ""},
            "mail": {"type": "str", "default": ""},
            "mail_report": {"type": "str", "choices": list(MAIL_REPORT_CHOICES)},
            "remove_unused_dependencies": {"type": "bool"},
            "remove_new_unused_dependencies": {"type": "bool"},
            "remove_unused_kernel_packages": {"type": "bool"},
            "minimal_steps": {"type": "bool"},
            "install_on_shutdown": {"type": "bool"},
            "auto_fix_interrupted_dpkg": {"type": "bool"},
            "syslog_enable": {"type": "bool"},
            "verbose": {"type": "bool"},
            "periodic": {"type": "dict", "default": {}},
            "validate": {"type": "bool", "default": True},
            "mode": {"type": "raw", "default": "0644"},
            "owner": {"type": "str", "default": "root"},
            "group": {"type": "str", "default": "root"},
        },
        mutually_exclusive=[("name", "path")],
        required_one_of=[("name", "path")],
        supports_check_mode=True,
    )

    path = _resolve_path(module)

    if module.params["state"] == "absent":
        changed = remove_file(module, path)
        module.exit_json(changed=changed, path=path)

    content = _render(module)
    if module.params["validate"]:
        validate_apt_conf(module, content)

    changed = write_file(
        module,
        path,
        content.encode("utf-8"),
        mode=module.params["mode"],
        owner=module.params["owner"],
        group=module.params["group"],
    )
    module.exit_json(changed=changed, path=path)


if __name__ == "__main__":
    main()
