.. _ansible_collections.ak1ra_lab.general.docsite.architecture:

Architecture
============

The collection is a set of independent roles with explicit variable contracts.
Playbooks compose the roles; the role ``meta/main.yaml`` files keep
``dependencies: []`` so consumers control the order. A role may still use
``ansible.builtin.import_role`` internally when one implementation builds on
another; those imports are part of the role contract, not a collection-wide
dependency graph.

Role families
-------------

- **Host baseline and packages**: ``debian_base``, ``apt_install``,
  ``docker``.
- **Build and install**: ``go_build``, ``pyproject_install``.

Each role owns its files and units. Roles do not share a global state
directory except where their READMEs document the same target path.

Host baseline and packages
--------------------------

``debian_base`` applies the Debian archive and security configuration,
unattended-upgrades policy, baseline packages, and optional host bootstrap
settings. ``apt_install`` is the reusable third-party repository layer: it
manages the keyring, a DEB822 source, optional pinning, unattended-upgrades,
package installation or hold, and legacy ``.list`` cleanup.

``docker`` is a composition role: it imports ``apt_install`` for the Docker
repository and its package list, then manages ``/etc/docker/daemon.json``, the
``docker`` group, and the Docker service. It does not duplicate the APT
repository logic.

Build and install
-----------------

``go_build`` runs on the controller by default (``hosts: localhost`` in the
example playbooks). It clones a repository into a controller-local work tree,
builds a Go binary, and exposes ``go_build_binary_path`` for a follow-up copy or
install task. A metadata stamp makes repeated runs skip unchanged builds.

``pyproject_install`` installs a Python package into a target virtual
environment. The ``local`` source builds a wheel on the controller with
``uv build --wheel``, copies it to the managed host, installs it with ``pip``,
and removes the remote temporary wheel. The ``pypi`` and ``testpypi`` sources
install directly from an index.

Facts and outputs
-----------------

- ``go_build_binary_path``, ``go_build_repo_dir``, and
  ``go_build_stamp_path`` are exposed for follow-up tasks.
- ``cpu_info`` exposes ``ansible_facts['cpu']``, including ``flags``,
  ``microarch_levels``, and ``microarch_level``. ``github_releases_info``
  accepts that level through ``asset_microarch`` when a repository publishes
  per-microarchitecture builds.

Documentation contract
----------------------

The role argument specs in ``roles/<role>/meta/argument_specs.yml`` are the
canonical variable reference. The role READMEs keep the narrative and deployed
artifact descriptions. Generated role pages in :doc:`collection_index` come
from the argument specs; plugin pages come from the in-code ``DOCUMENTATION``
blocks.
