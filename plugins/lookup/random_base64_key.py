# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Lookup plugin: generate base64 key material on the control node.

Useful for pre-shared keys whose decoded length must equal a cipher key
length. The key bytes come from ``secrets.token_bytes`` (the operating
system's cryptographically secure random number generator), so the decoded
key has full entropy per byte.
"""

from __future__ import annotations

DOCUMENTATION = r"""
---
name: random_base64_key
short_description: Generate base64-encoded random key material
description:
  - Returns base64 of O(bytes) random bytes generated with
    C(secrets.token_bytes) (the operating system's cryptographically secure
    random number generator).
  - The result decodes to exactly O(bytes) bytes; the standard base64
    alphabet and padding are used.
  - The lookup generates a new key on every evaluation; store the result
    (for example with the C(ansible.builtin.set_fact) module) when it must
    stay stable across template re-renders and repeated runs.
options:
  bytes:
    description: Number of random bytes the decoded key contains.
    type: int
    default: 32
author:
  - ak1ra (@ak1ra-lab)
"""

EXAMPLES = r"""
- name: Generate the base64 key for a 2022-blake3-aes-128-gcm cipher
  ansible.builtin.set_fact:
    shadowsocks_password: "{{ lookup('ak1ra_lab.general.random_base64_key', bytes=16) }}"
"""

RETURN = r"""
_raw:
  description: Base64-encoded random key material.
  type: list
  elements: str
"""

import base64
import secrets
from typing import Any

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

DEFAULT_BYTES = 32


class LookupModule(LookupBase):
    """Generate base64 key material; see the module docstring."""

    def run(
        self,
        terms: list[Any],
        variables: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        if terms:
            raise AnsibleLookupError("random_base64_key takes no positional terms; pass bytes as a keyword argument")

        size = kwargs.get("bytes", DEFAULT_BYTES)
        try:
            size = int(size)
        except (TypeError, ValueError):
            raise AnsibleLookupError(f"bytes must be an integer, got {size!r}") from None
        if size <= 0:
            raise AnsibleLookupError(f"bytes must be a positive integer, got {size!r}")

        return [base64.b64encode(secrets.token_bytes(size)).decode("ascii")]
