.. _ansible_collections.ak1ra_lab.general.docsite.modules:

Modules
=======

The collection provides two custom modules. The generated reference pages
:doc:`cpu_info_module` and :doc:`github_releases_info_module` are built from
their ``DOCUMENTATION``, ``EXAMPLES``, and ``RETURN`` blocks; this page
explains how they fit together.

github_releases_info
--------------------

``github_releases_info`` queries the GitHub releases API for a repository,
normalizes the asset list, and selects the best matching artifact for the
current host. It is a read-only info module: downloading is left to follow-up
tasks such as ``ansible.builtin.get_url``.

Selection order:

1. Exact ``asset_url`` or ``asset_name``.
2. Regex and substring narrowing.
3. Compatibility filtering by OS, architecture, distribution, libc, and
   microarchitecture level.
4. Preferred asset family ordering.
5. Preference for more specific distribution, libc, OS, architecture, and
   microarchitecture matches.

With ``require_digest`` enabled (the default), the module fails when neither an
explicit checksum nor a GitHub-provided digest is available. The returned
``download_url`` and ``download_checksum`` can be passed directly to
``ansible.builtin.get_url``:

.. code-block:: yaml

   - name: Inspect the latest GitHub release assets
     ak1ra_lab.general.github_releases_info:
       repo: sharkdp/bat
     register: github_releases_result

   - name: Download the selected release asset
     ansible.builtin.get_url:
       url: "{{ github_releases_result.download_url }}"
       dest: /tmp/{{ github_releases_result.selected_asset.name }}
       checksum: "{{ github_releases_result.download_checksum }}"
       mode: "0644"

To inspect normalized metadata without downloading, call the module with
``asset_name_regex`` (or ``asset_name_contains``) and read the returned
``assets``, ``candidate_assets``, and ``selected_asset`` values:

.. code-block:: yaml

   - name: Inspect release assets matching a regex
     ak1ra_lab.general.github_releases_info:
       repo: sharkdp/bat
       asset_name_regex: 'linux.*x86_64.*\.tar\.gz$'
     register: bat_release

   - name: Show all normalized assets and the selected asset
     ansible.builtin.debug:
       var: bat_release.assets

The generated reference (:doc:`github_releases_info_module`) includes the full
example sequence. For microarchitecture-aware selection, run ``cpu_info`` first
and pass its ``microarch_level`` through ``asset_microarch`` as shown below.

cpu_info
--------

``cpu_info`` collects CPU capability facts from the managed host and exposes
them as ``ansible_facts['cpu']`` (also returned under the ``cpu`` key):

- ``architecture``, ``vendor``, ``model``, ``logical_cpus``
- ``flags``: raw CPU capability flags, intersected across all logical CPUs
- ``microarch_levels``: supported x86-64 psABI levels (``x86-64-v1`` through
  ``x86-64-v4``)
- ``microarch_level``: the highest supported level

On Linux the facts are parsed from ``/proc/cpuinfo``. On other platforms
``architecture`` is still reported, while ``vendor``, ``model``,
``logical_cpus``, ``flags``, and the microarchitecture fields are empty or
zero. Facts from third-party collections are not part of
``ansible.builtin.setup``, so run ``cpu_info`` explicitly:

.. code-block:: yaml

   - name: Collect CPU capability facts
     ak1ra_lab.general.cpu_info:
     register: cpu_facts

   - name: Feed the detected level into asset selection
     ak1ra_lab.general.github_releases_info:
       repo: example/tool
       asset_microarch: "{{ ansible_facts['cpu']['microarch_level'] }}"

The same reference is available offline with
``ansible-doc ak1ra_lab.general.<module>`` against an installed collection.
