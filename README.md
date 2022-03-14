Documentation
=============


[![image](https://img.shields.io/travis/TankerHQ/cloudmesh-bar.svg?branch=main)](https://travis-ci.org/TankerHQ/cloudmesn-bar)

[![image](https://img.shields.io/pypi/pyversions/cloudmesh-bar.svg)](https://pypi.org/project/cloudmesh-bar)

[![image](https://img.shields.io/pypi/v/cloudmesh-bar.svg)](https://pypi.org/project/cloudmesh-bar/)

[![image](https://img.shields.io/github/license/TankerHQ/python-cloudmesh-bar.svg)](https://github.com/TankerHQ/python-cloudmesh-bar/blob/main/LICENSE)

see cloudmesh.cmd5

* https://github.com/cloudmesh/cloudmesh.cmd5


**Sample YAML File**

This command requires a YAML file which is configured for the host and gpu.
The YAML file also points to the desired slurm template.

```python
slurm_template: 'slurm_template.slurm'

sbatch_setup:
  <hostname>-<gpu>:
    - card_name: "a100"
    - time: "05:00:00"
    - num_cpus: 6
    - num_gpus: 1

  rivanna-v100:
    - card_name: "v100"
    - time: "06:00:00"
    - num_cpus: 6
    - num_gpus: 1


```
