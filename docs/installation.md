# Installation

The intended consumption model is a project-local `requirements.yaml` pinned to
either a Git tag or a commit.

## Git-Pinned Install

```yaml
---
collections:
  - name: https://github.com/ak1ra-lab/ansible-collection-general.git
    type: git
    version: v0.1.0
```

Install into a repository-local collections path:

```shell
ansible-galaxy collection install -r requirements.yaml -p ./.ansible/collections
```

`version` can be a tag, branch, or commit-ish. Use tags or immutable commits for
CI and normal day-to-day consumption.

## Repository Development Workflow

When working inside this repository, refresh the repo-local installed copy
before running `ansible-lint`, `ansible-playbook --syntax-check`, or any local
playbook that imports `ak1ra_lab.general.*`:

```shell
just install
```

This uses the checked-in `justfile` to run:

```shell
ansible-galaxy collection install --upgrade --collections-path .ansible/collections .
```

The repository's `ansible.cfg` expects collection resolution through
`./.ansible/collections`, so local validation should target that installed copy.

Do not create a symlink at
`./.ansible/collections/ansible_collections/ak1ra_lab/general` inside this
repository. That layout can conflict with `ansible-lint` and
`ansible-galaxy collection build`.

## Cross-Repository Local Development

For cross-repository local development, install from the local source checkout:

```shell
ansible-galaxy collection install /path/to/ansible-collection-general -p ./.ansible/collections --force
```

Re-run the install after source changes so the consumer repository sees the
updated collection content.

## Consumer Usage

Reference shared roles by their fully qualified collection names:

```yaml
- name: Build restic on localhost
  ansible.builtin.import_role:
    name: ak1ra_lab.general.go_build
  vars:
    go_build_repo_url: https://github.com/restic/restic.git
    go_build_output_name: restic
```

```yaml
- name: Install application package
  ansible.builtin.import_role:
    name: ak1ra_lab.general.pyproject_install
  vars:
    pyproject_install_source: local
    pyproject_install_package_name: example-package
```
