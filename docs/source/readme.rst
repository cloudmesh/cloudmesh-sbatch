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
ability to support parameterization in a scheduled task. While there are
facilities in place to execute jobs on an Array, the ability to do
permutation based experments are limited to what you integrate into your
own batch script. Even then, parameterization of values are only made
availabile as environment variables, which can be limited depending on
your OS or selected programming language. In many cases limitations set
by the deployment trhough the compute center also hinder optimal use
while restrictions are placed on duration and number of parallel
accessible resources. In some cases these restrictions are soo
established that removing them is impractical and takes weks to
implement on temporary basis.

Cloudmesh Sbatch is a framework that wraps the SLURM batch processor
into a templated framework such that experiments can be generated based
on configuration files focusing on the livecycle of generating many
permutations of experiments with standard tooling, so that you can focus
more on modeling your experiments than how to orchestrate them with
tools. A number of batch scripts can be generated that than can be
executed according to center policies.

Dependencies
------------

When you install cloudmesh-sbatch, you will also be installing a minimum
baseline of the ``cms`` command (as part of the Cloudmesh ecosystem).
For more details on Cloudmesh, see its documentation on `read the
docs <https://cloudmesh.github.io/cloudmesh-manual/>`__. However all
instalation can be done thorugh pip. After instalation, you will need to
initialize cloudmesh with the command

.. code:: bash

   $ cms help

While SLURM is not needed to run the ``cloudmesh sbatch`` command, the
generated output will not exectue unless your system has slurm installed
and you are able to run jobs via the ``slurm sbatch`` command.

Documentation
-------------

Running Cloudmesh SBatch
~~~~~~~~~~~~~~~~~~~~~~~~

The ``cloudmesh sbatch`` command takes one of two forms of execution. It
is started with

.. code:: bash

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``generate`` command is used to generate your experiments based upon
either a passed configuration file, or via CLI arguments. You can issue
the command using either of the below forms:

.. code:: text

   cms sbatch generate SOURCE --name=NAME [--verbose] [--mode=MODE] [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT]
   cms sbatch generate --setup=FILE [SOURCE] [--verbose] [--mode=MODE]  [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT] [--name=NAME]

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

example:

::

   cms sbatch slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
   sbatch slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]"
   # ERROR: Importing python not yet implemented
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

-  https://slurm.schedmd.com/pdfs/summary.pdf
