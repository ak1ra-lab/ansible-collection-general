# 角色

## acme_dns

部署 acme-dns 服务: 一个带有 RESTful HTTP API 的受限 DNS 服务器, 用于处理 ACME DNS-01 质询.

主要输入:

- `acme_dns_domain`
- `acme_dns_server_ip`
- `acme_dns_nsadmin`
- `acme_dns_api_tls`
- `acme_dns_listen`
- `acme_dns_api_ip`
- `acme_dns_api_port`
- `acme_dns_api_corsorigins`

主要结果:

- 通过 `go_build` 在 localhost 上编译 acme-dns Go 二进制文件并部署到目标主机
- systemd 服务运行 acme-dns DNS 服务器
- 配置文件中包含 domain、NS 记录、API TLS 设置和日志配置

部署后, 需要在上游 DNS 服务商处添加委托记录, 将 acme-dns 域名委托给 acme-dns 服务器.

A 记录的数量取决于 `acme_dns_nsname` 是否与 `acme_dns_domain` 不同.

**当 `acme_dns_nsname != acme_dns_domain`**（使用独立的域名服务器名称）,
需要三条记录:

> 示例取值 `acme_dns_server_ip: xx.xx.xx.xx`,
> `acme_dns_domain: auth.acme-dns.example.com`,
> `acme_dns_nsname: ns1.acme-dns.example.com`:

| 类型 | 名称                                  | 指向                          | 用途               |
|------|---------------------------------------|-------------------------------|--------------------|
| A    | `auth.acme-dns.example.com`           | `xx.xx.xx.xx`                 | zone apex 可达     |
| NS   | `auth.acme-dns.example.com`           | `ns1.acme-dns.example.com`    | 委托区域           |
| A    | `ns1.acme-dns.example.com`            | `xx.xx.xx.xx`                 | 域名服务器 glue    |

**当 `acme_dns_nsname == acme_dns_domain`**（默认）, NS 委托给自己,
一条 A 记录同时承担 glue 和 zone apex 两个角色:

> 示例取值 `acme_dns_server_ip: xx.xx.xx.xx`,
> `acme_dns_domain: auth.acme-dns.example.com`,
> `acme_dns_nsname: auth.acme-dns.example.com`（默认值）:

| 类型 | 名称                                  | 指向               | 用途                       |
|------|---------------------------------------|--------------------|----------------------------|
| A    | `auth.acme-dns.example.com`           | `xx.xx.xx.xx`      | glue + zone apex           |
| NS   | `auth.acme-dns.example.com`           | `auth.acme-dns.example.com` | 委托区域          |

没有这些记录, `*.auth.acme-dns.example.com` 的 DNS-01 质询查询将无法到达 acme-dns 实例.

## acme_dns_register

向 acme-dns 服务端注册客户端, 将凭据持久化到 host_vars 目录, 并可选择创建 `_acme-challenge` CNAME 记录.

主要输入:

- `acme_dns_register_server_url`
- `acme_dns_register_username`
- `acme_dns_register_password`
- `acme_dns_register_subdomain`
- `acme_dns_register_acme_domains`
- `acme_dns_register_cloudflare_api_token`
- `acme_dns_register_cloudflare_zone_token`

主要结果:

- 通过 POST /register 注册 acme-dns 账户
- 凭据持久化到配置目录中的 `acme_dns_credentials.yaml`
- 通过 Cloudflare API 添加 `_acme-challenge` CNAME 记录, 或提示手动创建

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
