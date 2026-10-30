# pyproject_install

> Role documentation generated from [`meta/argument_specs.yml`](meta/argument_specs.yml)
> is the canonical variable reference. This README covers purpose, deployed
> artifacts, and operational notes.

Install a Python package into a target virtual environment.

The role supports three sources:

- `local`: build a wheel on `localhost` with `uv build --wheel`, copy it to the
  target host, and install it with `pip`
- `pypi`: install from the public PyPI index
- `testpypi`: install from TestPyPI with PyPI as an extra index

## Requirements

`uv` must be available on the controller when using the `local` source. The
target needs a Python interpreter with `venv` support; the role installs the
distro packages needed by `ansible.builtin.pip` before creating the environment.

## Variables

The canonical variable reference is generated from `meta/argument_specs.yml` in
the collection documentation.

## Notes

- The virtual environment is created at `pyproject_install_venv_dir` (by
  default `/var/lib/<package>/venv`).
- A locally built wheel is copied to the target temporary directory and removed
  after installation. Local installs use force-reinstall so version bumps from
  a git rebase are not skipped.
