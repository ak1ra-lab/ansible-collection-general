# Modules

The collection provides two custom modules. The generated
[module reference](ak1ra_lab.general/index.md) is built from their
`DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks; the sections below explain
how they fit together.

## github_releases_info

`github_releases_info` queries the GitHub releases API for a repository,
normalizes the asset list, and selects the best matching artifact for the
current host. It is a read-only info module: downloading is left to follow-up
tasks such as `ansible.builtin.get_url`.

Selection order:

1. Exact `asset_url` or `asset_name`.
2. Regex and substring narrowing.
3. Compatibility filtering by OS, architecture, distribution, libc, and
   microarchitecture level.
4. Preferred asset family ordering.
5. Preference for more specific distribution, libc, OS, architecture, and
   microarchitecture matches.

With `require_digest` enabled (the default), the module fails when neither an
explicit checksum nor a GitHub-provided digest is available. The returned
`download_url` and `download_checksum` can be passed directly to
`ansible.builtin.get_url`:

```yaml
- name: Inspect the latest GitHub release assets
  ak1ra_lab.general.github_releases_info:
    repo: sharkdp/bat
  register: github_releases_result

- name: Download the selected release asset
  ansible.builtin.get_url:
    url: "{{ github_releases_result.download_url }}"
    dest: /tmp/{{ github_releases_result.selected_asset.name }}
    checksum: "{{ github_releases_result.download_checksum }}"
    mode: "0644"
```

Use [`playbooks/github_releases/inspect-latest.yaml`](https://github.com/ak1ra-lab/ansible-collection-general/blob/master/playbooks/github_releases/inspect-latest.yaml)
to inspect normalized release metadata without downloading. The playbook runs
`cpu_info` first and passes the detected microarchitecture level.

## cpu_info

`cpu_info` collects CPU capability facts from the managed host and exposes
them as `ansible_facts['cpu']` (also returned under the `cpu` key):

- `architecture`, `vendor`, `model`, `logical_cpus`
- `flags`: raw CPU capability flags, intersected across all logical CPUs
- `microarch_levels`: supported x86-64 psABI levels (`x86-64-v1` through
  `x86-64-v4`)
- `microarch_level`: the highest supported level

On Linux the facts are parsed from `/proc/cpuinfo`. On other platforms
`architecture` is still reported, while `vendor`, `model`, `logical_cpus`,
`flags`, and the microarchitecture fields are empty or zero. Facts from
third-party collections are not part of `ansible.builtin.setup`, so run
`cpu_info` explicitly:

```yaml
- name: Collect CPU capability facts
  ak1ra_lab.general.cpu_info:
  register: cpu_facts

- name: Feed the detected level into asset selection
  ak1ra_lab.general.github_releases_info:
    repo: example/tool
    asset_microarch: "{{ ansible_facts['cpu']['microarch_level'] }}"
```

## Reference

- [`github_releases_info` reference](ak1ra_lab.general/module/github_releases_info.md)
- [`cpu_info` reference](ak1ra_lab.general/module/cpu_info.md)

The generated `cpu_info` page lists the top-level `cpu` return; its nested
fields are documented above.

The same reference is available offline with
`ansible-doc ak1ra_lab.general.<module>` against an installed collection.
