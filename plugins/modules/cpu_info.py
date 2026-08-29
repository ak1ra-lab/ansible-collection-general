from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ak1ra_lab.general.plugins.module_utils.cpu import (
    collect_cpu_facts,
)

DOCUMENTATION = r"""
---
module: cpu_info
short_description: Collect CPU capability facts for the managed host
description:
  - Gathers CPU flags and standardized microarchitecture levels from the
    managed host and exposes them as facts under C(cpu).
  - On Linux the facts are parsed from C(/proc/cpuinfo); on other platforms
    O(flags) and the microarchitecture fields are returned empty while the
    basic fields stay populated.
  - The C(flags) value is the intersection across all logical CPUs, so it is
    safe to treat as the capability set of the whole machine.
options: {}
notes:
  - Facts from third-party collections cannot be gathered by
    M(ansible.builtin.setup); run this module explicitly and either register
    its return value or read C(ansible_facts['cpu']) afterwards.
  - The microarchitecture levels currently cover the x86-64 psABI levels
    C(x86-64-v1) through C(x86-64-v4). The return shape is architecture
    agnostic, so other architectures can add their own level tables later.
author:
  - ak1ra
"""

EXAMPLES = r"""
- name: Collect CPU capability facts
  ak1ra_lab.general.cpu_info:
  register: cpu_facts

- name: Show the detected microarchitecture level
  ansible.builtin.debug:
    var: cpu_facts.cpu.microarch_level

- name: Feed the detected level into github_releases_info asset selection
  ak1ra_lab.general.github_releases_info:
    repo: example/tool
    asset_microarch: "{{ ansible_facts['cpu']['microarch_level'] }}"
"""

RETURN = r"""
cpu:
  description: CPU capability facts. Also exposed as C(ansible_facts['cpu']).
  returned: always
  type: dict
  contains:
    architecture:
      description: Machine architecture as reported by C(platform.machine()).
      returned: always
      type: str
      sample: x86_64
    vendor:
      description: CPU vendor identifier. Empty on non-x86 hosts.
      returned: always
      type: str
      sample: AuthenticAMD
    model:
      description: CPU model name. Empty on hosts that do not report one.
      returned: always
      type: str
      sample: AMD Ryzen 9 5900X 12-Core Processor
    logical_cpus:
      description: Number of logical CPU entries found.
      returned: always
      type: int
      sample: 24
    flags:
      description:
        - Raw CPU capability flags (intersected across logical CPUs). Empty on
          platforms without a parseable source.
      returned: always
      type: list
      elements: str
      sample: [avx2, fma, sse4_2]
    microarch_levels:
      description:
        - Mapping of standardized microarchitecture levels to whether the CPU
          supports them. Empty on architectures without a level table.
      returned: always
      type: dict
      sample:
        x86-64-v1: true
        x86-64-v2: true
        x86-64-v3: true
        x86-64-v4: false
    microarch_level:
      description:
        - Highest supported microarchitecture level, for example
          C(x86-64-v3). Empty when no level table applies.
      returned: always
      type: str
"""


def main() -> None:
    module = AnsibleModule(argument_spec={}, supports_check_mode=True)
    cpu = collect_cpu_facts()
    module.exit_json(changed=False, ansible_facts={"cpu": cpu}, cpu=cpu)


if __name__ == "__main__":
    main()
