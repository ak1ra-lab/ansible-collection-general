# Show available recipes
default:
    @just --list --unsorted

# Run all available recipes
all: lint typecheck unit-test ansible-lint docs-lint docs-build

# Sync development dependencies (may update uv.lock if pyproject.toml changed)
sync *ARGS:
    uv sync {{ARGS}} --group dev

# Lint and format collection Python plugins and tests
lint:
    uv run ruff check --fix plugins/ tests/
    uv run ruff format plugins/ tests/

# Run static type checks with mypy
# Resolving the collection-namespace imports requires a fresh install
typecheck: ansible-collection-install
    uv run mypy plugins/ tests/

# Show the tox-ansible environment matrix
tox-list:
    uv run tox list --ansible

# Run one tox-ansible environment, e.g. `just tox sanity-py3.13-2.21`
tox env='sanity-py3.13-2.21':
    uv run tox -e {{env}} --ansible

# Run the unit tests in an isolated tox-ansible environment
unit-test:
    uv run tox -e unit-py3.13-2.21 --ansible

# Install project-local Ansible collection (lint, mypy and docs only; Molecule
# installs the collection and its test dependencies itself)
ansible-collection-install:
    mkdir -p .ansible/collections
    uv run ansible-galaxy collection install --force --collections-path .ansible/collections .

# Lint all Ansible content with ansible-lint (production profile)
ansible-lint:
    uv run ansible-lint

# Lint module and plugin documentation with antsibull-docs
docs-lint: ansible-collection-install
    uv run --group lint antsibull-docs lint-collection-docs --plugin-docs --validate-collection-refs self --skip-rstcheck .

# Check that every role has a docs page, nav entry, and index link
docs-check:
    uv run --group docs python scripts/check_docs.py

# Build the documentation site into site/
docs-build: ansible-collection-install docs-check
    ANSIBLE_COLLECTIONS_PATH="$PWD/.ansible/collections" NO_MKDOCS_2_WARNING=1 uv run --group docs mkdocs build --strict

# Serve the documentation site locally
docs-serve: ansible-collection-install docs-check
    ANSIBLE_COLLECTIONS_PATH="$PWD/.ansible/collections" NO_MKDOCS_2_WARNING=1 uv run --group docs mkdocs serve

# Run every Molecule scenario.  Scenarios are flat and each one owns its
# containers; no MOLECULE_GLOB or project-local collection pre-install.
molecule-test:
    uv run molecule test --all

# Run one Molecule scenario, e.g. `just molecule-test-one apt_install_basic`
molecule-test-one scenario:
    uv run molecule test -s {{scenario}}

# Syntax-check every scenario's converge playbook
molecule-syntax:
    uv run molecule syntax --all

# List the Molecule scenarios
molecule-list:
    uv run molecule list

# Remove build artifacts
clean:
    rm -rf .ansible/ .molecule/ .cache/ .ruff_cache/ site/
    find plugins/ -type f -name "*.pyc" -delete
    find plugins/ -type d -name "__pycache__" -delete
