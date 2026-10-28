# Show available recipes
default:
    @just --list --unsorted

# Run all available recipes
all: lint typecheck ansible-lint docs-lint docs-build

# Sync development dependencies (may update uv.lock if pyproject.toml changed)
sync *ARGS:
    uv sync {{ARGS}} --group dev

# Lint and format collection Python plugins
lint:
    uv run ruff check --fix plugins/
    uv run ruff format plugins/

# Run static type checks with Astral ty
# Resolving the collection-namespace imports requires a fresh install
typecheck: ansible-collection-install
    uv run ty check plugins/

# Install project-local Ansible collection
ansible-collection-install:
    mkdir -p .ansible/collections
    ansible-galaxy collection install --force --collections-path .ansible/collections .

# Install the collections required by the Molecule scenarios
ansible-requirements-install:
    mkdir -p .ansible/collections
    ansible-galaxy collection install -r requirements.yaml -p .ansible/collections

# Lint all Ansible content with ansible-lint (production profile)
ansible-lint:
    ansible-lint

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

# Run every Molecule scenario (nested scenarios need the recursive glob)
molecule-test: ansible-collection-install ansible-requirements-install
    MOLECULE_GLOB='extensions/molecule/**/molecule.yml' molecule test --all

# Run one Molecule scenario, e.g. `just molecule-test-one apt_install/basic`
molecule-test-one scenario: ansible-collection-install ansible-requirements-install
    MOLECULE_GLOB='extensions/molecule/**/molecule.yml' molecule test -s {{scenario}}

# List the Molecule scenarios
molecule-list:
    MOLECULE_GLOB='extensions/molecule/**/molecule.yml' molecule list

# Create the shared test containers used by every scenario
molecule-create: ansible-collection-install ansible-requirements-install
    molecule create

# Remove the shared test containers
molecule-destroy:
    molecule destroy

# Remove build artifacts
clean:
    rm -rf .ansible/ .molecule/ .cache/ .ruff_cache/ site/
    find plugins/ -type f -name "*.pyc" -delete
    find plugins/ -type d -name "__pycache__" -delete
