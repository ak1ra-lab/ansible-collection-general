.. _ansible_collections.ak1ra_lab.general.docsite.getting-started:

.. _ansible_collections.ak1ra_lab.general.docsite.getting_started:

Getting started
===============

Install the collection
----------------------

The collection is currently consumed from Git; it is not published to Galaxy.
Create a ``requirements.yaml`` in the consuming repository:

.. code-block:: yaml

   ---
   collections:
     - name: git+https://github.com/ak1ra-lab/ansible-collection-general.git
       version: master

Install it into the project-local collections path:

.. code-block:: shell

   ansible-galaxy collection install -r requirements.yaml -p ./.ansible/collections

The consuming repository's ``ansible.cfg`` should put that path at the front of
``collections_path``. Pin a tag or commit instead of ``master`` for
reproducible deployments.

Control-node requirements
-------------------------

- ``ansible-core >= 2.19.0`` (``meta/runtime.yml``) and Python ``>= 3.11``.
- The collection dependencies are installed automatically by
  ``ansible-galaxy``: ``ansible.posix`` and ``community.general``.
- ``go`` is required on the controller for ``go_build``, which builds binaries
  on ``localhost``.
- ``uv`` is required on the controller for ``pyproject_install`` when
  ``pyproject_install_source: local`` builds a wheel from a local project.

Managed-node requirements
-------------------------

The APT-based roles target Debian 12 and Debian 13. The Molecule scenarios use
the systemd-enabled ``debian:12`` and ``debian:13`` container images from
`ak1ra-lab/docker-systemd <https://github.com/ak1ra-lab/docker-systemd>`_.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Role
     - Requirements
   * - ``apt_install``
     - Debian; root privileges for the keyring, APT source files, and package
       installation.
   * - ``debian_base``
     - Debian; root privileges.
   * - ``docker``
     - Debian; root privileges. The role imports ``apt_install`` for the
       Docker repository and installs the Docker packages.
   * - ``go_build``
     - ``go`` on the controller; the build runs on ``localhost``, not the
       managed host.
   * - ``pyproject_install``
     - A target Python environment; ``uv`` on the controller for local wheel
       builds.

First playbooks
---------------

The bundled entry points accept ``playbook_hosts``; each playbook's ``hosts``
expression documents its default inventory group.

.. code-block:: shell

   ansible-playbook playbooks/debian-base-defaults.yaml -e playbook_hosts=web
   ansible-playbook playbooks/docker-vps.yaml -e playbook_hosts=web

The example playbooks under ``playbooks/apt_install/`` and
``playbooks/go_build/`` are runnable recipes for specific packages and build
targets. See :doc:`playbooks` for the layout and examples.

Next steps
----------

- :doc:`architecture` for how the role families compose.
- :doc:`collection_index` for the generated role and plugin reference.
- :doc:`modules` and :doc:`lookups` for the collection plugins.
