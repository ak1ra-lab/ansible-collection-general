# 模块

`plugins/modules/` 下的模块 `DOCUMENTATION` 块是参数, 返回值和示例参考的权威来源.
针对已安装的 collection 副本, 使用 `ansible-doc ak1ra_lab.general.<module>`
获取每个模块的完整参考.

## github_releases

查询某个仓库的 GitHub releases API, 规范化资产列表, 为当前主机选择最匹配的产物,
并可选地在受管主机上下载该资产.

工作流说明:

1. 精确匹配 `asset_url` 或 `asset_name`
2. 正则和子串收窄
3. 按 OS, 架构, 发行版和 libc 自动进行兼容性过滤
4. 首选资产族排序
5. 优先选择更具体的发行版, libc, OS 和架构匹配

使用 `playbooks/github_releases/inspect-latest.yaml`
可在不下载的情况下查看规范化的 release 元数据和所选资产.

inspect 任务示例:

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

该模块有意止步于发现, 选择和下载. 它不会安装 `.deb`, `.rpm` 或解压后的归档内容.
