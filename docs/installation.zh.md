# 安装

推荐的使用方式是在项目本地的 `requirements.yaml` 中固定到某个 Git 标签或提交.

## 固定到 Git 版本安装

```yaml
---
collections:
  - name: https://github.com/ak1ra-lab/ansible-collection-general.git
    type: git
    version: v0.1.0
```

安装到仓库本地的 collections 路径:

```shell
ansible-galaxy collection install -r requirements.yaml -p ./.ansible/collections
```

`version` 可以是标签, 分支或 commit-ish. 在 CI 和日常使用中, 请使用标签或不可变的提交.

## 仓库开发工作流

克隆到任意位置:

```shell
git clone https://github.com/ak1ra-lab/ansible-collection-general.git
```

安装 collection 本身 (playbook 通过 FQCN 引用角色, 因此必须安装本地 collection):

```shell
ansible-galaxy collection install --force --collections-path .ansible/collections .
```

`requirements.yaml` 中的依赖 (`ansible.posix`, `community.general`) 通常已经在
user level 存在, 因此本地开发一般只需安装 collection 自身即可.

## 使用方用法

通过完全限定的 collection 名称引用共享角色:

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
