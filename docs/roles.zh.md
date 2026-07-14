# 角色

## debian_base

为新配置的主机应用 Debian 或 Ubuntu 基线.

主要输入:

- `debian_base_apt_repo_debian_uris`
- `debian_base_apt_repo_debian_security_uris`
- `debian_base_apt_repo_debian_backports_enabled`
- `debian_base_unattended_upgrade_updates_enabled`
- `debian_base_unattended_upgrade_automatic_reboot_enabled`
- `debian_base_apt_force_ipv4_enabled`
- `debian_base_tcp_bbr_enabled`
- `debian_base_custom_sshd_config_enabled`
- `debian_base_custom_sysctl_conf_enabled`
- `debian_base_apt_packages`

主要结果:

- 以 DEB822 格式渲染 Debian 归档和安全仓库
- 为稳定版更新和可选的 backports 开启 unattended-upgrades
- 安装日常主机管理所需的基线软件包
- 可选的 TCP BBR, SSH 加固条目, sysctl 调优, 以及 qemu-guest-agent 启用

## go_build

在 `localhost` 上从 Git 仓库构建 Go 项目, 并缓存元数据标记, 使得仅在输入变化时才重新构建.

主要输入:

- `go_build_repo_url`
- `go_build_output_name`
- `go_build_repo_version`
- `go_build_package`
- `go_build_static`
- `go_build_goos`
- `go_build_goarch`

主要输出:

- `go_build_repo_dir`
- `go_build_binary_path`
- `go_build_stamp_path`

## pyproject_install

将 Python 包安装到目标主机上的虚拟环境中.

支持的来源:

- `local`: 在 `localhost` 上用 `uv build --wheel` 构建 wheel, 复制到远程主机, 并用 `pip` 安装.
- `pypi`: 从公共 PyPI 索引安装.
- `testpypi`: 从 TestPyPI 安装, 并以 PyPI 作为额外索引.

主要输入:

- `pyproject_install_source`
- `pyproject_install_package_name`
- `pyproject_install_package_extras`
- `pyproject_install_local_project_root`
- `pyproject_install_venv_dir`
- `pyproject_install_remote_tmp_dir`
- `pyproject_install_system_packages`
