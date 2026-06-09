# Modules

Module `DOCUMENTATION` blocks under `plugins/modules/` are the source of truth
for argument, return-value, and example reference. Use `ansible-doc
ak1ra_lab.general.<module>` against an installed copy of the collection for the
full per-module reference.

## github_releases

Queries the GitHub releases API for a repository, normalizes the asset list,
selects the best matching artifact for the current host, and optionally
downloads that asset on the managed host.

Workflow notes:

1. Exact `asset_url` or `asset_name`
2. Regex and substring narrowing
3. Automatic compatibility filtering by OS, arch, distro, and libc
4. Preferred asset family ordering
5. Preference for more specific distro, libc, OS, and arch matches

Use `playbooks/github_releases/inspect-latest.yaml`
to inspect normalized release metadata and the selected asset without downloading.

Example inspect task:

```yaml
- name: Inspect the latest GitHub release assets
  ak1ra_lab.general.github_releases:
    repo: sharkdp/bat
    download: false
  register: github_releases_result

- name: Show the selected asset
  ansible.builtin.debug:
    var: github_releases_result.selected_asset
```

The module intentionally stops at discovery, selection, and download. It does
not install `.deb`, `.rpm`, or extracted archive contents.
