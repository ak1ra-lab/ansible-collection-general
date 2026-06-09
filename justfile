# Show available recipes
default:
    @just --list --unsorted

# Sync development dependencies for Python plugin work
sync *ARGS:
    uv sync {{ARGS}} --group dev

# Lint and format collection Python plugins
lint:
    uv run ruff check --fix plugins/
    uv run ruff format plugins/

# Build project-local Ansible collection
build:
    mkdir -p dist/
    ansible-galaxy collection build --force --output-path dist/ .

# Remove build artifacts
clean:
    rm -rf dist/ site/ .cache/ .ruff_cache/
    find plugins/ -type f -name "*.pyc" -delete
    find plugins/ -type d -name "__pycache__" -delete
