# Roles

## go_build

Builds a Go project from a Git repository on `localhost` and caches a metadata
stamp so repeated runs rebuild only when inputs change.

Primary inputs:

- `go_build_repo_url`
- `go_build_output_name`
- `go_build_repo_version`
- `go_build_package`
- `go_build_static`
- `go_build_goos`
- `go_build_goarch`

Primary outputs:

- `go_build_repo_dir`
- `go_build_binary_path`
- `go_build_stamp_path`

## pyproject_install

Installs a Python package into a virtual environment on the target host.

Supported sources:

- `local`: build a wheel with `uv build --wheel` on `localhost`, copy it to the remote host, and install it with `pip`.
- `pypi`: install from the public PyPI index.
- `testpypi`: install from TestPyPI with PyPI as an extra index.

Primary inputs:

- `pyproject_install_source`
- `pyproject_install_package_name`
- `pyproject_install_package_extras`
- `pyproject_install_local_project_root`
- `pyproject_install_venv_dir`
- `pyproject_install_remote_tmp_dir`
- `pyproject_install_system_packages`
