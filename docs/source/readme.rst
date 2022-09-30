Cloudmesh Sbatch
================

A general purpose HPC Template and Experiment management system

Background
----------

Hyper Performance Computation Clusters (HPCs) are designed around a
timesharing principle and are powered by queue-based execution
ecosystems such as SchedMD’s
`SLURM <https://slurm.schedmd.com/overview.html>`__ and IBM’s Platform
Load Sharing Facility
(`LSF <https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=overview-lsf-introduction>`__).
While these ecosystems provide a great deal of control and extension for
planning, scheduling, and batching jobs, they are limited in their
ability to support parameterization in a scheduled task when system restrictions
have been implemented by the system
administrative staff. These restrictions in time and space
may not even allow the user to use
build in functionality to execute jobs on an array of jobs and thus eliminate
the ability to do
permutation-based experiments are limited to what you integrate into your
own batch script. Even then, parameterization of values is only made
available as environment variables, which can be too restrictive.
We found that in many cases limitations set
by the deployment through the computing center hinder optimal use
while restrictions are placed on duration and number of parallel
accessible resources. In some cases these restrictions are soo
established that removing them is impractical and takes weeks to
implement temporarily.

Cloudmesh-sbatch is a framework that wraps the batch processor (for SLURM and LSF)
into a templated framework such that experiments can be generated based
on configuration files focusing on the live cycle of generating many
permutations of experiments with standard tooling, so that you can focus
more on modeling your experiments rather than on how to orchestrate them with
tools that break due to the restrictions put in place.
A number of batch scripts can be generated that can be
executed according to center policies.


Instalation
-----------

When you install cloudmesh-sbatch, you will also be installing cloudmesh
shell (`cms`) as part of the Cloudmesh ecosystem. It allows cloudmesh sbatch to
be run either in commandline or scripted mode.

The instalation is easy via pip

.. code-block:: console

   $ pip install cloudmesh-sbatch
   $ cms help

Please do not forget to say `cms help` the first time you use cms as it set
it up with some default values.
The SLURM or LSF commands are  not needed to be installed locally, as we assume that
all access to the batch environment is conducted indirectly and remotely through `ssh`.

In case you like to install cloudmesh-sbatch from source we have a convenient
program that downloads all cloudmesh repositories its depeds on.

.. code-block:: console

   $ python -m venv ~/ENV3
   $ source ~/ENV#/bin/activate
   $ pip install pip -U
   $ mkdir cm
   $ cd cm
   $ pip install cloudmesh-installer
   $ cloudmesh-installer get sbatch
   $ cms help


NOTE THIS IS OUTDATED FROM HERE ON AND NEEDS TO BE UPDATED


Running Cloudmesh SBatch
------------------------

The ``cloudmesh sbatch`` command takes one of two forms of execution. It
is started with

.. code-block:: console

   $ cms sbatch <command> <parameters>

Where the command invokes a partiuclar action and parameters include a
number of parameters for the command These commands allow you to inspect
the generated output to confirm your parameterization functions as
expected and as intended.

In general, configuration arguments that appear in multiple locations
are prioritized in the following order (highest priority first)

1. CLI Arguments with ``cms sbatch``
2. Configuration Files
3. Preset values

Generating Experiments with the CLI
-----------------------------------

The ``generate`` command is used to generate your experiments based upon
either a passed configuration file, or via CLI arguments. You can issue
the command using either of the below forms:



.. code:: text

   cms sbatch generate SOURCE
                       --name=NAME
                       [--verbose]
                       [--mode=MODE]
                       [--config=CONFIG]
                       [--attributes=PARAMS]
                       [--out=DESTINATION]
                       [--dryrun]
                       [--noos]
                       [--nocm]
                       [--dir=DIR]
                       [--experiment=EXPERIMENT]

If you have prepared a configuration file that conforms to the schema
defined in `Setup Config <#setup-config>`__, then you can use the second
form which overrides the default values.

-  ``--name=NAME`` - Supplies a name for this experiment. Note that the
   name must not match any existing files or directories where you are
   currently executing the command

-  ``--verbose`` - Enables additional logging useful when
   troubleshooting the program.

-  ``--mode=MODE`` - specifies how the output should be generated. One
   of: f,h,d.

   -  ``f`` or ``flat`` - specifies a “flat” mode, where slurm scripts
      are generated in a flattened structure, all in one directory.
   -  ``h`` or ``hierarchical`` - specifies a “hierarchical” mode, where
      experiments are nested into unique directories from each other.
   -  ``d`` or ``debug`` - instructs the command to not generate any
      output.

-  ``--config=CONFIG`` - specifies key-value pairs to be used across all
   files for substitution. This can be a python, yaml, or json file.

-  ``--attributes=PARAMS`` - specifies key-value pairs that can be
   listed at the command line and used as substitution across all
   experiments. Note this command leverages `cloudmesh’s parameter
   expansion
   specification <https://cloudmesh.github.io/cloudmesh-manual/autoapi/cloudmeshcommon/cloudmesh/common/parameter/index.html>`__
   for different types of expansion rules.

-  ``--out=DESTINATION`` - specifies the directory to write the
   generated scripts out to.

-  ``--dryrun`` - Runs the command without performing any operations

-  ``--noos`` - Prevents the interleaving of OS environemnt variables
   into the subsitution logic

-  ``--dir=DIR`` - specifies the directory to write the generated
   scripts out to.

-  ``--experiment=EXPERIMENT`` - specifies a listing of key-value
   parameters that establish a unique experiment for each combination of
   values (a cartisian product across all values for each key).

-  ``--setup=FILE`` - provides all the above configuration options
   within a configuration file to simplify executions.

Form 2 - Generating Submission Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: text

   sbatch generate submit --name=NAME [--verbose]

This command uses the output of the `generate
command <#command-1---generating-experiments>`__ and generates a shell
script that can be used to submit your previously generated outputs to
SLURM as a sequence of sbatch commands.

-  ``--name=NAME`` - specifies the name used in the `generate
   command <#command-1---generating-experiments>`__. The generate
   command will inspect the ``<NAME>.json`` file and build the necessary
   commands to run all permutations that the cloudmesh sbatch command
   generated.

Note that this command only generates the script, and you must run the
outputted file in your shell for the commands to be issued to SLURM and
run your jobs.

**Sample YAML File**

This command requires a YAML file which is configured for the host and
gpu. The YAML file also points to the desired slurm template.

.. code:: python

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

Example::

   cms sbatch slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
   sbatch slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]"
   epoch=1 x=1 y=10  sbatch example/slurm.sh
   epoch=1 x=1 y=11  sbatch example/slurm.sh
   epoch=1 x=4 y=10  sbatch example/slurm.sh
   epoch=1 x=4 y=11  sbatch example/slurm.sh
   epoch=2 x=1 y=10  sbatch example/slurm.sh
   epoch=2 x=1 y=11  sbatch example/slurm.sh
   epoch=2 x=4 y=10  sbatch example/slurm.sh
   epoch=2 x=4 y=11  sbatch example/slurm.sh
   epoch=3 x=1 y=10  sbatch example/slurm.sh
   epoch=3 x=1 y=11  sbatch example/slurm.sh
   epoch=3 x=4 y=10  sbatch example/slurm.sh
   epoch=3 x=4 y=11  sbatch example/slurm.sh
   Timer: 0.0022s Load: 0.0013s sbatch slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]"



Cheatsheet
~~~~~~~~~~

- SLURM: https://slurm.schedmd.com/pdfs/summary.pdf
- LSF: https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=started-quick-reference
