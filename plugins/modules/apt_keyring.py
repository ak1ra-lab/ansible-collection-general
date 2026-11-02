# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: apt_keyring
short_description: Manage an APT repository keyring file
description:
  - Write or remove a local APT keyring file from a URL, inline content, or a
    member extracted from a Debian package.
  - The module never installs packages. Use O(deb) with O(member) to extract a
    keyring from a keyring package without adding the package to the dpkg
    database or trusting the key globally through C(/etc/apt/trusted.gpg.d).
  - The resulting path is intended for the C(Signed-By) field of a DEB822
    source or a one-line C(sources.list) entry.
options:
  dest:
    description:
      - Absolute path of the keyring file.
      - Use C(/etc/apt/keyrings) for operator-managed keys and
        C(/usr/share/keyrings) for keys managed by packages.
    required: true
    type: path
  state:
    description:
      - Whether the keyring file should exist.
    type: str
    choices: [present, absent]
    default: present
  url:
    description:
      - URL of a keyring file.
      - Exactly one of O(url), O(content), O(content_base64), and O(deb) must
        be set when O(state=present).
    type: str
    default: ''
  content:
    description:
      - Inline keyring text, typically an ASCII-armored OpenPGP public key.
    type: str
    default: ''
  content_base64:
    description:
      - Base64-encoded keyring bytes, suitable for binary OpenPGP keyrings.
    type: str
    default: ''
  deb:
    description:
      - URL of a Debian package that contains a keyring file.
      - Requires O(member).
    type: str
    default: ''
  member:
    description:
      - Path of the keyring file inside the package named by O(deb).
      - For example C(usr/share/keyrings/vendor-archive-keyring.gpg).
    type: str
    default: ''
  checksum:
    description:
      - Optional checksum for O(url) or O(deb), in C(algorithm:value) form or
        as a bare hexadecimal digest.
      - For O(url), an existing destination file is checked against the
        checksum before deciding whether a download is needed.
    type: str
    default: ''
  force:
    description:
      - Re-download O(url) or O(deb) even when O(dest) already exists.
      - A URL with O(checksum) is not re-downloaded when the existing file
        already matches the checksum.
    type: bool
    default: false
  mode:
    description:
      - File mode of the keyring.
    type: raw
    default: '0644'
  owner:
    description:
      - Owner of the keyring file.
    type: str
    default: root
  group:
    description:
      - Group of the keyring file.
    type: str
    default: root
  validate_certs:
    description:
      - Validate TLS certificates when downloading O(url) or O(deb).
    type: bool
    default: true
  timeout:
    description:
      - HTTP timeout in seconds for O(url) and O(deb).
    type: int
    default: 30
notes:
  - APT reads C(Signed-By) keyrings as the C(_apt) user. Keep the file readable
    by that user; the default mode C(0644) is suitable.
  - This module does not import keys into C(trusted.gpg) or
    C(trusted.gpg.d); it writes an isolated keyring for C(Signed-By).
author:
  - ak1ra (@ak1ra-lab)
"""

EXAMPLES = r"""
- name: Install a keyring from a URL
  ak1ra_lab.general.apt_keyring:
    url: https://www.postgresql.org/media/keys/ACCC4CF8.asc
    checksum: "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    dest: /etc/apt/keyrings/postgresql-pgdg.asc

- name: Install an ASCII-armored keyring from inline content
  ak1ra_lab.general.apt_keyring:
    content: |
      -----BEGIN PGP PUBLIC KEY BLOCK-----
      ...
      -----END PGP PUBLIC KEY BLOCK-----
    dest: /etc/apt/keyrings/example.asc

- name: Extract a keyring from a keyring package without installing it
  ak1ra_lab.general.apt_keyring:
    deb: https://www.deb-multimedia.org/pool/main/d/deb-multimedia-keyring/deb-multimedia-keyring_2024.9.1_all.deb
    member: usr/share/keyrings/deb-multimedia-keyring.pgp
    checksum: "sha256:8dc6cbb266c701cfe58bd1d2eb9fe2245a1d6341c7110cfbfe3a5a975dcf97ca"
    dest: /etc/apt/keyrings/deb-multimedia.gpg

- name: Remove a managed keyring
  ak1ra_lab.general.apt_keyring:
    dest: /etc/apt/keyrings/example.asc
    state: absent
"""

RETURN = r"""
dest:
  description: Path of the managed keyring.
  returned: always
  type: str
  sample: /etc/apt/keyrings/example.asc
format:
  description: Detected keyring format.
  returned: when the keyring exists or was written
  type: str
  sample: armored
checksum:
  description: SHA-256 checksum of the managed keyring bytes.
  returned: when the keyring exists or was written
  type: str
  sample: 9f2c...
changed:
  description: Whether the keyring changed.
  returned: always
  type: bool
"""

import os
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ak1ra_lab.general.plugins.module_utils.apt import (
    data_checksum,
    decode_keyring_content,
    download_bytes,
    extract_deb_member,
    is_armored_key,
    parse_checksum,
    read_file,
    remove_file,
    verify_checksum,
    write_file,
)

SOURCES = ("url", "content", "content_base64", "deb")


def _select_source(module: AnsibleModule) -> str:
    selected = [name for name in SOURCES if module.params[name]]
    if not selected:
        module.fail_json(msg=("exactly one of url, content, content_base64, and deb must be set when state=present"))
    source = selected[0]
    if source == "deb" and not module.params["member"]:
        module.fail_json(msg="member is required when deb is set")
    if source != "deb" and module.params["member"]:
        module.fail_json(msg="member is only valid with deb")
    return source


def _download_deb(module: AnsibleModule) -> bytes:
    data = download_bytes(
        module,
        module.params["deb"],
        timeout=module.params["timeout"],
    )
    verify_checksum(module, data, module.params["checksum"], module.params["deb"])
    fd, path = tempfile.mkstemp(dir=module.tmpdir, suffix=".deb")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        return extract_deb_member(module, path, module.params["member"])
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _existing_keyring(module: AnsibleModule, source: str) -> bytes | None:
    existing = read_file(module, module.params["dest"])
    if not existing:
        return None
    if module.params["force"]:
        return None
    if source == "url" and module.params["checksum"]:
        try:
            algorithm, expected = parse_checksum(module.params["checksum"])
        except ValueError as exc:
            module.fail_json(msg=f"invalid checksum: {exc}")
        if data_checksum(existing, algorithm) != expected:
            return None
    return existing


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "dest": {"type": "path", "required": True},
            "state": {
                "type": "str",
                "choices": ["present", "absent"],
                "default": "present",
            },
            "url": {"type": "str", "default": ""},
            "content": {"type": "str", "default": ""},
            "content_base64": {"type": "str", "default": ""},
            "deb": {"type": "str", "default": ""},
            "member": {"type": "str", "default": ""},
            "checksum": {"type": "str", "default": ""},
            "force": {"type": "bool", "default": False},
            "mode": {"type": "raw", "default": "0644"},
            "owner": {"type": "str", "default": "root"},
            "group": {"type": "str", "default": "root"},
            "validate_certs": {"type": "bool", "default": True},
            "timeout": {"type": "int", "default": 30},
        },
        mutually_exclusive=[list(SOURCES)],
        supports_check_mode=True,
    )

    dest = module.params["dest"]
    if not os.path.isabs(dest):
        module.fail_json(msg="dest must be an absolute path")

    if module.params["state"] == "absent":
        changed = remove_file(module, dest)
        module.exit_json(changed=changed, dest=dest, format="", checksum="")

    source = _select_source(module)
    existing = _existing_keyring(module, source)

    if existing is not None:
        data = existing
    elif source == "url":
        data = download_bytes(
            module,
            module.params["url"],
            timeout=module.params["timeout"],
        )
        verify_checksum(module, data, module.params["checksum"], module.params["url"])
    elif source == "deb":
        data = _download_deb(module)
    else:
        data = decode_keyring_content(
            module,
            content=module.params["content"],
            content_base64=module.params["content_base64"],
        )
        verify_checksum(module, data, module.params["checksum"], source)

    if not data:
        module.fail_json(msg="keyring content is empty")

    changed = write_file(
        module,
        dest,
        data,
        mode=module.params["mode"],
        owner=module.params["owner"],
        group=module.params["group"],
    )
    module.exit_json(
        changed=changed,
        dest=dest,
        format="armored" if is_armored_key(data) else "binary",
        checksum=data_checksum(data),
    )


if __name__ == "__main__":
    main()
