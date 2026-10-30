.. _ansible_collections.ak1ra_lab.general.docsite.playbooks:

Playbooks
=========

The collection ships thin playbook entry points and runnable examples. They
set privileges, gather facts, and apply roles; the variable contracts stay in
the role argument specs.

Layout
------

- ``playbooks/<role>.yaml`` is a top-level entry point for one role or a small
  composition.
- ``playbooks/<role>/*.yaml`` contains example invocations for specific build
  or release targets.
- Every example accepts ``playbook_hosts``; the default is documented in the
  playbook's ``hosts`` expression.

Entry points
------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Playbook
     - Behavior
   * - ``debian-base-defaults.yaml``
     - Applies the ``debian_base`` defaults profile to ``localhost``.
   * - ``debian-base-vps.yaml``
     - Applies the VPS profile (BBR, automatic reboot) to ``localhost``.
   * - ``docker-defaults.yaml``
     - Imports the defaults profile, then applies ``docker``.
   * - ``docker-vps.yaml``
     - Imports the VPS profile, then applies ``docker`` with unattended
       upgrades.

Examples
--------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Directory
     - Purpose
   * - ``playbooks/apt_install/``
     - Third-party repository recipes (Grafana, HashiCorp, Microsoft, NVIDIA,
       PostgreSQL, Tailscale, and others). Each file is a complete
       ``apt_install`` invocation.
   * - ``playbooks/go_build/``
     - Controller-side Go builds for tools such as ``restic``, ``nexttrace``,
       ``nali``, ``yq``, and ``yamlfmt``, including copy or capability steps.
   * - ``playbooks/github_releases/``
     - ``inspect-latest.yaml`` prints normalized release metadata and the
       selected asset; ``python-build-standalone.yaml`` installs a standalone
       Python build.
   * - ``playbooks/debian-base-*.yaml``, ``playbooks/docker-*.yaml``
     - Baseline profiles for a fresh host.

Common commands
---------------

.. code-block:: shell

   # Inspect the latest release assets for a repository
   ansible-playbook playbooks/github_releases/inspect-latest.yaml \
     -e github_releases_repo=sharkdp/bat

   # Build restic on the controller
   ansible-playbook playbooks/go_build/restic.yaml -e playbook_hosts=localhost

   # Add the Grafana APT repository and install Grafana
   ansible-playbook playbooks/apt_install/grafana.yaml -e playbook_hosts=web

   # Apply the VPS baseline and Docker
   ansible-playbook playbooks/docker-vps.yaml -e playbook_hosts=web

The playbook files are the source of truth for the exact variables and
follow-up tasks. Browse the
`playbooks directory <https://github.com/ak1ra-lab/ansible-collection-general/tree/master/playbooks>`_
for the full list.
