# Modules

Module `DOCUMENTATION` blocks under `plugins/modules/` are the source of truth
for argument, return-value, and example reference. Use `ansible-doc
ak1ra_lab.general.<module>` against an installed copy of the collection for the
full per-module reference.

## github_releases_info

Queries the GitHub releases API for a repository, normalizes the asset list,
and selects the best matching artifact for the current host. The module is a
read-only info module: it stops at discovery and selection, and leaves the
actual download to follow-up tasks such as `ansible.builtin.get_url`.

Workflow notes:

1. Exact `asset_url` or `asset_name`
2. Regex and substring narrowing
3. Automatic compatibility filtering by OS, arch, distro, libc, and
   microarchitecture level
4. Preferred asset family ordering
5. Preference for more specific distro, libc, OS, arch, and microarch matches

Use `playbooks/github_releases/inspect-latest.yaml`
to inspect normalized release metadata and the selected asset without
downloading. The playbook runs `cpu_info` first and passes the detected
microarchitecture level, which also disambiguates repositories that publish
per-level builds with names like `tool-linux-amd64-v3-<version>`.

Example inspect task:

```yaml
- name: Inspect the latest GitHub release assets
  ak1ra_lab.general.github_releases_info:
    repo: sharkdp/bat
  register: github_releases_result

- name: Show the selected asset
  ansible.builtin.debug:
    var: github_releases_result.selected_asset
```

Download with `ansible.builtin.get_url` using the returned
`download_url` and `download_checksum` (`algorithm:value` form). With
`require_digest` enabled (the default), the module fails early when no
checksum is available, so `get_url` can always verify the download.

```yaml
- name: Download the selected release asset
  ansible.builtin.get_url:
    url: "{{ github_releases_result.download_url }}"
    dest: /tmp/{{ github_releases_result.selected_asset.name }}
    checksum: "{{ github_releases_result.download_checksum }}"
    mode: "0644"
```

## cpu_info

Collects CPU capability facts from the managed host and exposes them as
`ansible_facts['cpu']` (also returned under the `cpu` key):

- `architecture`, `vendor`, `model`, `logical_cpus`
- `flags`: raw CPU capability flags, intersected across logical CPUs
- `microarch_levels`: standardized level support map, e.g.
  `x86-64-v1`..`x86-64-v4` for x86-64 hosts
- `microarch_level`: the highest supported level, e.g. `x86-64-v3`

On Linux the facts are parsed from `/proc/cpuinfo`; other platforms return
empty `flags` and microarchitecture fields. The level tables are registered
per architecture, so other architectures can add their own levels later.

```yaml
- name: Collect CPU capability facts
  ak1ra_lab.general.cpu_info:
  register: cpu_facts

- name: Feed the detected level into asset selection
  ak1ra_lab.general.github_releases_info:
    repo: example/tool
    asset_microarch: "{{ ansible_facts['cpu']['microarch_level'] }}"
```

Note that facts from third-party collections cannot be gathered by
`ansible.builtin.setup`; run `cpu_info` explicitly in your play.
