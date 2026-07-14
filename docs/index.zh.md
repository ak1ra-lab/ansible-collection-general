# ak1ra_lab.general

`ak1ra_lab.general` 是一个共享的 Ansible collection, 包含可复用的角色和自定义模块,
供多个 `ak1ra-lab` 仓库使用.

## 角色

- `debian_base`: 为主机应用 Debian 或 Ubuntu 基线, 包含精选软件包, apt 仓库默认配置,
  无人值守升级, 以及常见的主机初始化设置.
- `go_build`: 在 `localhost` 上克隆并构建 Go 项目, 并暴露构建产物的二进制路径供后续任务使用.
- `pyproject_install`: 从本地 wheel, PyPI 或 TestPyPI 构建或安装 Python 包到目标虚拟环境中.

## 模块

- `github_releases`: 查询 GitHub release 元数据, 规范化资产名称, 为本地平台选择匹配的资产,
  并可选地在受管主机上下载该资产.

用法详见 [安装](installation.md), [角色](roles.md) 和 [模块](modules.md).
