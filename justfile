# Show available recipes
default:
    @just --list --unsorted

# Install project-local Ansible collections
install:
    mkdir -p .ansible/collections
    ansible-galaxy collection install --upgrade --collections-path .ansible/collections .

# Build project-local Ansible collection
build:
    mkdir -p dist/
    ansible-galaxy collection build --force --output-path dist/ .

# Remove build artifacts
clean:
    rm -rf dist/ site/ .cache/
