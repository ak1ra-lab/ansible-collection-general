.. _ansible_collections.ak1ra_lab.general.docsite.playbooks:

Playbooks
=========

This collection is a library. It ships reusable roles, modules, and lookup
plugins, but no runnable playbooks or operational scripts.

Operational playbooks, inventory examples, and helper scripts live in the
separate `ansible-playbooks-infra
<https://github.com/ak1ra-lab/ansible-playbooks-infra>`_ repository. That
repository composes the roles from this collection and pins a released
collection version.

The external repository includes:

- Debian baseline and Docker profile entry points.
- ``apt_install`` recipes for third-party repositories.
- Controller-side ``go_build`` and GitHub release recipes.
- Example inventory and site variables.

Install ``ak1ra_lab.general`` from Galaxy as described in
:doc:`getting-started`, then run the playbooks from that repository or from
your own playbook project. The role argument specs in
:doc:`collection_index` remain the variable reference.
