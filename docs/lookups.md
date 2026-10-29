# Lookup plugins

The collection provides three controller-side lookups for generating
secrets. They use the operating system's cryptographically secure random
number generator (`secrets`) and return a fresh value on every evaluation.
Store the result (for example with `ansible.builtin.set_fact`) when it must
stay stable across template re-renders and repeated runs.

| Lookup | Purpose |
| --- | --- |
| `ak1ra_lab.general.random_password` | Random password from an alphabet (default: 32 ASCII letters/digits). |
| `ak1ra_lab.general.random_base64_key` | Base64-encoded random key material with a configurable decoded byte length (default: 32 bytes). |
| `ak1ra_lab.general.random_uuid` | Random RFC 4122 version 4 UUID. |

## Examples

```yaml
- name: Generate listener credentials
  ansible.builtin.set_fact:
    listener_password: "{{ lookup('ak1ra_lab.general.random_password', length=24) }}"
    listener_uuid: "{{ lookup('ak1ra_lab.general.random_uuid') }}"
    cipher_key: "{{ lookup('ak1ra_lab.general.random_base64_key', bytes=16) }}"

- name: Generate a password from a custom alphabet
  ansible.builtin.debug:
    msg: "{{ lookup('ak1ra_lab.general.random_password', alphabet='0123456789abcdef') }}"
```

`random_password` and `random_base64_key` accept keyword arguments only;
positional terms are rejected. `random_uuid` takes no arguments. Invalid
lengths, byte counts, or alphabets raise `AnsibleLookupError` instead of
silently generating a weaker value.

## Unit tests

The lookups are covered by `tests/unit/plugins/lookup/` and run with
`ansible-test units` from a standard collection layout.
