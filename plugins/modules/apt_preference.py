# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: apt_preference
short_description: Manage APT preference and pinning records
description:
  - Render one or more apt_preferences(5) records into a file under
    C(/etc/apt/preferences.d), or remove that file.
  - >-
    The module accepts full release field names such as C(origin) and
    C(codename) and normalizes them to the single-letter fields that APT
    actually understands in a C(Pin: release) line.
  - >-
    Use C(pin.site) for C(Pin: origin), which matches a repository hostname
    and is not the same as the C(Origin:) field from a Release file.
options:
  name:
    description:
      - Basename of the preferences file in C(/etc/apt/preferences.d).
      - Mutually exclusive with O(path).
    type: str
  path:
    description:
      - Full path of the preferences file.
      - Mutually exclusive with O(name).
    type: path
  state:
    description:
      - Whether the preferences file should exist.
    type: str
    choices: [present, absent]
    default: present
  entries:
    description:
      - Preferences records rendered in order.
      - Required when O(state=present).
    type: list
    elements: dict
    default: []
  mode:
    description:
      - File mode of the preferences file.
    type: raw
    default: '0644'
  owner:
    description:
      - Owner of the preferences file.
    type: str
    default: root
  group:
    description:
      - Group of the preferences file.
    type: str
    default: root
notes:
  - APT parses files in C(/etc/apt/preferences.d) in alphanumeric order. Keep
    role-owned files together under a stable prefix such as C(90).
  - A C(Pin-Priority) of C(0) has undefined behaviour in APT and is rejected.
  - The C(Package:) field accepts package names, globs, and slash-delimited
    regular expressions, as documented in apt_preferences(5).
author:
  - ak1ra (@ak1ra-lab)
"""

EXAMPLES = r"""
- name: Prefer packages from a vendor repository
  ak1ra_lab.general.apt_preference:
    name: 90example
    entries:
      - packages: ["*"]
        pin:
          site: packages.example.invalid
        priority: 900

- name: Pin a release by its Release file fields
  ak1ra_lab.general.apt_preference:
    name: 90pgdg
    entries:
      - packages: ["caddy"]
        pin:
          release:
            origin: apt.postgresql.org
            codename: trixie-pgdg
        priority: 900

- name: Keep backports below the stable archive
  ak1ra_lab.general.apt_preference:
    name: 90debian-backports
    entries:
      - packages: ["linux-*", "initramfs-tools"]
        pin:
          release:
            codename: trixie-backports
        priority: 500

- name: Remove a preferences file
  ak1ra_lab.general.apt_preference:
    name: 90example
    state: absent
"""

RETURN = r"""
path:
  description: Path of the managed preferences file.
  returned: always
  type: str
  sample: /etc/apt/preferences.d/90example
changed:
  description: Whether the preferences file changed.
  returned: always
  type: bool
"""

import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ak1ra_lab.general.plugins.module_utils.apt import (
    PREFERENCES_DIR,
    remove_file,
    render_preference_entries,
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
            validate_filename(name, extension=".pref")
        except ValueError as exc:
            module.fail_json(msg=str(exc))
        return os.path.join(PREFERENCES_DIR, name)

    if not os.path.isabs(path):
        module.fail_json(msg="path must be an absolute path")
    try:
        validate_filename(os.path.basename(path), extension=".pref")
    except ValueError as exc:
        module.fail_json(msg=str(exc))
    return path


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
            "entries": {"type": "list", "elements": "dict", "default": []},
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

    try:
        content = render_preference_entries(module.params["entries"])
    except ValueError as exc:
        module.fail_json(msg=str(exc))

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
