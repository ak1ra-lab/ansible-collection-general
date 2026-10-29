# Copyright: (c) 2026, ak1ra <ak1ra.komj@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for plugins/lookup/random_uuid.py."""

from __future__ import annotations

import uuid

import pytest
from ansible.errors import AnsibleLookupError
from ansible_collections.ak1ra_lab.general.plugins.lookup.random_uuid import (
    LookupModule,
)


def generate() -> str:
    return LookupModule().run([], {})[0]


def test_canonical_uuid4() -> None:
    value = generate()
    parsed = uuid.UUID(value)
    assert parsed.version == 4
    assert parsed.variant == uuid.RFC_4122
    assert str(parsed) == value


def test_new_uuid_on_every_evaluation() -> None:
    assert generate() != generate()


def test_arguments_rejected() -> None:
    with pytest.raises(AnsibleLookupError):
        LookupModule().run(["ignored"], {})
    with pytest.raises(AnsibleLookupError):
        LookupModule().run([], {}, length=32)
