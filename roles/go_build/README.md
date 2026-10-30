# roles/go_build

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Ansible role that builds a Go command on **localhost** from a git repository with
`git clone` and `go build`, keeping build work off remote hosts that may have
limited CPU.

All build tasks run with `delegate_to: localhost` and `run_once: true`. The role
uses an isolated local source checkout and build caches under `go_build_base_dir`.
If `go_build_repo_dir` is left empty, the checkout path is derived at runtime and
preserves the repository host and path. For example,
`https://github.com/example/project.git` and `git@github.com:example/project.git`
both resolve to `{{ go_build_base_dir }}/src/github.com/example/project`.

After the build, the fact `go_build_binary_path` is set on every target host
pointing to the built binary on localhost.

## Requirements

`go` must be present in localhost `PATH`. The role fails immediately if it is not
found.

## Variables

The canonical variable reference is generated from `meta/argument_specs.yml` in
the collection documentation.

## Output Facts

After the role runs every target host will have:

```yaml
go_build_repo_dir: /path/to/checkout
go_build_chdir: /path/to/checkout/subdir   # absolute; equals go_build_repo_dir when no subdir was requested
go_build_binary_path: "{{ go_build_base_dir }}/bin/{{ go_build_output_name }}"
go_build_stamp_path: "{{ go_build_base_dir }}/.{{ go_build_output_name }}.build-meta"
```

Use `go_build_binary_path` in subsequent tasks to copy the binary to the remote
host. `go_build_repo_dir` and `go_build_chdir` are inputs as well as outputs:
the role resolves them internally and publishes the absolute values, so they
can be passed as `include_role`/`import_role` `vars:` without being shadowed by
`set_fact`.

## Lightweight repo pattern

For projects like caddyserver/caddy where custom builds only need a `main.go`
with plugin imports (not the full upstream source), create a minimal repo with
just `main.go` and `go.mod`.  Example structure:

```
ak1ra-lab/caddy-build/
  main.go    # imports caddy + desired DNS plugins
  go.mod     # module caddy
```

Then use standard git-clone workflow:

```yaml
- name: build caddy with DNS plugins
  ansible.builtin.import_role:
    name: ak1ra_lab.general.go_build
  vars:
    go_build_repo_url: "https://github.com/ak1ra-lab/caddy-build.git"
    go_build_output_name: "caddy"
```
