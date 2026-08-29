# 模块

`plugins/modules/` 下的模块 `DOCUMENTATION` 块是参数, 返回值和示例参考的权威来源.
针对已安装的 collection 副本, 使用 `ansible-doc ak1ra_lab.general.<module>`
获取每个模块的完整参考.

## github_releases_info

查询某个仓库的 GitHub releases API, 规范化资产列表, 为当前主机选择最匹配的产物.
该模块是只读的 info 模块: 它止步于发现和选择, 实际下载交给后续 task,
例如 `ansible.builtin.get_url`.

工作流说明:

1. 精确匹配 `asset_url` 或 `asset_name`
2. 正则和子串收窄
3. 按 OS, 架构, 发行版, libc 和微架构级别自动进行兼容性过滤
4. 首选资产族排序
5. 优先选择更具体的发行版, libc, OS, 架构和微架构匹配

使用 `playbooks/github_releases/inspect-latest.yaml`
可在不下载的情况下查看规范化的 release 元数据和所选资产.
该 playbook 会先运行 `cpu_info` 并把探测到的微架构级别传给资产选择,
从而消解发布多级别构建的仓库的歧义
(例如 `tool-linux-amd64-v3-<version>` 这类文件名).

inspect 任务示例:

```yaml
- name: Inspect the latest GitHub release assets
  ak1ra_lab.general.github_releases_info:
    repo: sharkdp/bat
  register: github_releases_result

- name: Show the selected asset
  ansible.builtin.debug:
    var: github_releases_result.selected_asset
```

使用返回的 `download_url` 和 `download_checksum` (`algorithm:value` 格式),
通过 `ansible.builtin.get_url` 完成下载. 开启 `require_digest` (默认) 时,
模块会在没有可用校验和的情况下提前失败, 从而保证 `get_url` 总能校验下载内容.

```yaml
- name: Download the selected release asset
  ansible.builtin.get_url:
    url: "{{ github_releases_result.download_url }}"
    dest: /tmp/{{ github_releases_result.selected_asset.name }}
    checksum: "{{ github_releases_result.download_checksum }}"
    mode: "0644"
```

## cpu_info

从受管主机采集 CPU 能力 facts, 以 `ansible_facts['cpu']` 暴露
(同时也通过 `cpu` key 返回):

- `architecture`, `vendor`, `model`, `logical_cpus`
- `flags`: 原始 CPU 能力 flags, 取所有逻辑 CPU 的交集
- `microarch_levels`: 标准化级别支持表, 例如 x86-64 主机的
  `x86-64-v1`..`x86-64-v4`
- `microarch_level`: 支持的最高级别, 例如 `x86-64-v3`

在 Linux 上 facts 解析自 `/proc/cpuinfo`; 其它平台返回空的 `flags`
和微架构字段. 级别表按架构注册, 其它架构未来可以添加自己的级别.

```yaml
- name: Collect CPU capability facts
  ak1ra_lab.general.cpu_info:
  register: cpu_facts

- name: Feed the detected level into asset selection
  ak1ra_lab.general.github_releases_info:
    repo: example/tool
    asset_microarch: "{{ ansible_facts['cpu']['microarch_level'] }}"
```

注意第三方 collection 的 facts 无法被 `ansible.builtin.setup` 采集,
需要在 play 中显式运行 `cpu_info`.
