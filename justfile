# Show available recipes
default:
    @just --list --unsorted

# Run all available recipes
all: lint typecheck docs-build

# Sync development dependencies (may update uv.lock if pyproject.toml changed)
sync *ARGS:
    uv sync {{ARGS}} --group dev

# Lint and format collection Python plugins
lint:
    uv run ruff check --fix plugins/
    uv run ruff format plugins/

# Run static type checks with Astral ty
typecheck:
    uv run ty check plugins/

# Serve documentation locally
docs-serve:
    uv run --group docs mkdocs serve

# Build documentation
docs-build:
    NO_MKDOCS_2_WARNING=1 uv run --group docs mkdocs build

# Install project-local Ansible collection
ansible-collection-install:
    mkdir -p .ansible/collections
    ansible-galaxy collection install --force --collections-path .ansible/collections .

# Build project-local Ansible collection
ansible-collection-build:
    mkdir -p .ansible/dist/
    ansible-galaxy collection build --force --output-path .ansible/dist/ .

# Remove build artifacts
clean:
    rm -rf .ansible/ site/ .cache/ .ruff_cache/
    find plugins/ -type f -name "*.pyc" -delete
    find plugins/ -type d -name "__pycache__" -delete
