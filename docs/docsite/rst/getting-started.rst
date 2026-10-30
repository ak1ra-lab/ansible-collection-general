.. _ansible_collections.ak1ra_lab.general.docsite.getting-started:

.. _ansible_collections.ak1ra_lab.general.docsite.getting_started:

Getting started
===============

Install the collection
----------------------

Install the released collection from Ansible Galaxy:

.. code-block:: shell

   ansible-galaxy collection install ak1ra_lab.general

Or pin it in a consumer ``requirements.yml``:

.. code-block:: yaml

   ---
   collections:
     - name: ak1ra_lab.general
       version: ">=0.4.0"

.. code-block:: shell

   ansible-galaxy collection install -r requirements.yml

Galaxy resolves ``ansible.posix`` and ``community.general`` from
``galaxy.yml`` automatically. The ``0.4.0`` release is the first Galaxy
release.

Control-node requirements
-------------------------

- ``ansible-core >= 2.19.0`` (``meta/runtime.yml``); tested with 2.19, 2.20,
  and 2.21 plus the weekly ``devel``/``milestone`` builds.
- Controller Python ``>= 3.11``; tested with 3.11, 3.12, and 3.13.
  ansible-core 2.20 and 2.21 additionally support Python 3.12-3.14.
- The collection dependencies are installed automatically by
  ``ansible-galaxy``: ``ansible.posix >= 1.5.4`` and
  ``community.general >= 8.0.0``.
- ``go`` is required on the controller for ``go_build``, which builds binaries
  on ``localhost``.
- ``uv`` is required on the controller for ``pyproject_install`` when
  ``pyproject_install_source: local`` builds a wheel from a local project.

Managed-node requirements
-------------------------

The APT-based roles target Debian 12 and Debian 13. Debian 12 ships target
Python 3.11 and Debian 13 ships target Python 3.13; the roles use the managed
node's ``/usr/bin/python3`` and do not require a newer interpreter. The
Molecule scenarios use the systemd-enabled ``debian:12`` and ``debian:13``
container images from
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

Runnable examples
-----------------

This collection is a library and does not ship runnable playbooks. Runnable
examples, inventory, and site playbooks live in the separate
`ansible-playbooks-infra <https://github.com/ak1ra-lab/ansible-playbooks-infra>`_
repository. Install the collection as above, then use that repository's
playbooks to compose these roles; see :doc:`playbooks` for the catalog.

To use a role from your own playbook project, install the collection and call
the role by its FQCN:

.. code-block:: yaml

   - name: Apply the Docker profile
     hosts: web
     become: true
     roles:
       - ak1ra_lab.general.docker

The role argument specs in ``roles/<role>/meta/argument_specs.yml`` generate
the canonical variable reference. Role READMEs keep purpose, deployed
artifacts, and examples. :doc:`collection_index` renders the generated role and
plugin reference.

Release order
-------------

``ak1ra_lab.general`` is released first. ``ak1ra_lab.certificate 0.1.0`` and
``ak1ra_lab.network 0.4.0`` both depend on ``ak1ra_lab.general >= 0.4.0`` and
must be released after it. See :doc:`changelog` for release notes.

Next steps
----------

- :doc:`architecture` for how the role families compose.
- :doc:`collection_index` for the generated role and plugin reference.
- :doc:`modules` and :doc:`lookups` for the collection plugins.
