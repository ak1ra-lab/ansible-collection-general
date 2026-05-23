# pyproject_install

Install a Python package into a target virtual environment.

The role supports three sources:

- `local`: build a wheel on `localhost` with `uv build --wheel`, copy it to the target host, and install it with `pip`
- `pypi`: install from the public PyPI index
- `testpypi`: install from TestPyPI with PyPI as an extra index

## Required Variables

- `pyproject_install_package_name`

## Common Variables

| Variable | Default | Description |
| --- | --- | --- |
| `pyproject_install_source` | `local` | Install source: `local`, `pypi`, or `testpypi` |
| `pyproject_install_package_extras` | empty string | Optional extras to install |
| `pyproject_install_local_project_root` | `{{ playbook_dir | dirname }}` | Local project root used for `uv build --wheel` |
| `pyproject_install_venv_dir` | `/var/lib/<package>/.venv` | Target virtual environment path |
| `pyproject_install_remote_tmp_dir` | `/tmp` | Remote temporary directory for copied wheel files |
| `pyproject_install_system_packages` | `[python3-venv]` | System packages installed before venv creation |
