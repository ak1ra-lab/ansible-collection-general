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

APT configuration modules
-------------------------

The APT modules manage one isolated piece of configuration each and never
install packages.

``apt_keyring`` writes a keyring from a URL, inline content, or a member
extracted from a Debian package. The ``deb`` + ``member`` form is useful for
keyring packages whose installation would also add a globally trusted key:

.. code-block:: yaml

   - name: Extract a keyring without installing the package
     ak1ra_lab.general.apt_keyring:
       deb: https://example.invalid/vendor-keyring.deb
       member: usr/share/keyrings/vendor-keyring.pgp
       checksum: "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
       dest: /etc/apt/keyrings/vendor.gpg

``apt_preference`` renders apt_preferences(5) records. Release field names are
normalized to the short forms APT requires; ``pin.site`` is the separate
``Pin: origin`` hostname matcher:

.. code-block:: yaml

   - name: Prefer packages from a vendor host
     ak1ra_lab.general.apt_preference:
       name: 90vendor
       entries:
         - packages: ["*"]
           pin:
             site: packages.example.invalid
           priority: 900

``apt_unattended_upgrades`` renders an apt.conf.d drop-in with origins
patterns, package rules, reboot settings, and APT::Periodic options. It
accepts both the full and abbreviated field names and validates the generated
file with ``apt-config``:

.. code-block:: yaml

   - name: Add a vendor origin to unattended-upgrades
     ak1ra_lab.general.apt_unattended_upgrades:
       name: vendor
       origins_patterns:
         - site: packages.example.invalid
       periodic:
         update_package_lists: 1
         unattended_upgrade: 1

The ``apt_repository`` role composes these modules with
``ansible.builtin.deb822_repository``. It installs the ``python3-debian``
module dependency when missing and refreshes the APT index after repository
changes; installation of repository packages and holds remain playbook tasks.

The same reference is available offline with
``ansible-doc ak1ra_lab.general.<module>`` against an installed collection.
