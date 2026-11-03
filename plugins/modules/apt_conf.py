# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: apt_conf
short_description: Manage APT configuration drop-in files
description:
  - Render or remove one APT configuration file under C(/etc/apt/apt.conf.d),
    or at an explicit absolute path.
  - Scalar values render as C(Name "value";).
  - >-
    Sequence values render one C(Name:: "value";) entry per item, which is
    APT's list syntax.
  - The module validates the generated file with C(apt-config) before writing
    it when O(validate) is true.
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
  options:
    description:
      - Mapping of APT configuration names to values.
      - A scalar value renders as C(Name "value";).
      - 'A list value renders as repeated C(Name:: "value";) entries.'
      - Required and non-empty when O(state=present).
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
  - APT reads the main C(/etc/apt/apt.conf) after the C(apt.conf.d) files, so
    a value in the main file can override a drop-in.
  - Pass a list for APT list options even when the list contains one item.
author:
  - ak1ra (@ak1ra-lab)
"""

EXAMPLES = r"""
- name: Configure an HTTP and HTTPS proxy for APT
  ak1ra_lab.general.apt_conf:
    name: 90ansible-debian-base-proxy
    options:
      Acquire::http::Proxy: http://proxy.example:3128
      Acquire::https::Proxy: http://proxy.example:3128

- name: Force APT to use IPv4
  ak1ra_lab.general.apt_conf:
    name: 99force-ipv4
    options:
      Acquire::ForceIPv4: true

- name: Add an unattended-upgrades origins pattern
  ak1ra_lab.general.apt_conf:
    name: 90unattended-upgrades-updates
    options:
      Unattended-Upgrade::Origins-Pattern:
        - origin=Debian,codename=${distro_codename}-updates

- name: Remove the role-owned proxy drop-in
  ak1ra_lab.general.apt_conf:
    name: 90ansible-debian-base-proxy
    state: absent
"""

RETURN = r"""
path:
  description: Path of the managed configuration file.
  returned: always
  type: str
  sample: /etc/apt/apt.conf.d/90ansible-debian-base-proxy
changed:
  description: Whether the configuration file changed.
  returned: always
  type: bool
"""

import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ak1ra_lab.general.plugins.module_utils.apt import (
    APT_CONF_DIR,
    remove_file,
    render_apt_conf_options,
    validate_apt_conf,
    validate_filename,
    write_file,
)


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


def _render(module: AnsibleModule) -> str:
    try:
        return render_apt_conf_options(
            module.params["options"],
            header="Managed by Ansible (ak1ra_lab.general.apt_conf).",
        )
    except ValueError as exc:
        module.fail_json(msg=str(exc))
    return ""


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
            "options": {"type": "dict", "default": {}},
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
