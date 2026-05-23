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

## Editable Workflow

For cross-repository local development, install from the local source checkout:

```shell
ansible-galaxy collection install /path/to/ansible-collection-general -p ./.ansible/collections --force
```

You can also create a symlink at:

```text
./.ansible/collections/ansible_collections/ak1ra_lab/general
```

pointing to the repository root.

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
