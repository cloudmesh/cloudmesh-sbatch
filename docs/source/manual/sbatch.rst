Command sbatch
==============

::

  Usage:
        sbatch generate submit --name=NAME [--job_type=JOB_TYPE] [--verbose]
        sbatch generate --source=SOURCE --name=NAME
                        [--out=OUT]
                        [--verbose]
                        [--mode=MODE]
                        [--config=CONFIG]
                        [--attributes=PARAMS]
                        [--output_dir=OUTPUT_DIR]
                        [--dryrun]
                        [--noos]
                        [--os=OS]
                        [--nocm]
                        [--source_dir=SOURCE_DIR]
                        [--experiment=EXPERIMENT]
                        [--flat]
        sbatch slurm start
        sbatch slurm stop
        sbatch slurm info

  sbatch allows the creation of parameterized batch
  scripts. The initial support includes slurm, but we intend
  also to support LSF. Parameters can be specified on the
  commandline or in configuration files. Configuration files
  can be formulated as json,yaml, python, or jupyter
  notebooks.

  Parameters defined in this file are then used in the slurm
  batch script and substituted with their values. A special
  parameter called experiment defines a number of variables
  that are permuted on when used allowing multiple batch
  scripts to be defined easily to conduct parameter studies.

  Please note that the setup flag is deprecated and is in
  future versions fully covered while just using the config
  file.

  Arguments:
      FILENAME       name of a slurm script generated with sbatch
      CONFIG_FILE    yaml file with configuration
      ACCOUNT        account name for host system
      SOURCE         name for input script slurm.in.sh, lsf.in.sh,
                     script.in.sh or similar
      PARAMS         parameter lists for experimentation
      GPU            name of gpu

  Options:
      -h                        help
      --config=CONFIG...        a list of comma seperated configuration
                                files in yaml or json format.
                                The endings must be .json or .yaml
      --type=JOB_TYPE           The method to generate submission scripts.
                                One of slurm, lsf. [default: slurm]
      --attributes=PARAMS       a list of coma separated attribute value pairs
                                to set parameters that are used. [default: None]
      --output_dir=OUTPUT_DIR   The directory where the result is written to
      --source_dir=SOURCE_DIR   location of the input directory [default: .]
      --account=ACCOUNT         TBD
      --gpu=GPU                 The name of the GPU. Tyoically k80, v100, a100, rtx3090, rtx3080
      --noos                    ignores environment variable substitution from the shell. This
                                can be helpfull when debugging as the list is quite lareg
      --nocm                    cloudmesh as a variable dictionary build in. Any vaiable referred to
                                by cloudmesh. and its name is replaced from the
                                cloudmesh variables
      --experiment=EXPERIMENT   This specifies all parameters that are used to create
                                permutations of them.
                                They are comma separated key value pairs
      --mode=MODE               one of "flat", "debug", "hierachical" can also just
                                use "f". "d", "h" [default: h]
      --name=NAME               name of the experiment configuration file
      --os=OS                   Selected OS variables
      --flat                    produce flatdict
      --dryrun                  flag to do a dryrun and not create files and
                                directories [default: False]
      --verbose                 Print more information when executing [default: False]

  Description:

    > Examples:
    >
    > cms sbatch generate slurm.in.sh --verbose \\
    >     --config=a.py,b.json,c.yaml \\
    >     --attributes=a=1,b=4 \\
    >     --dryrun --noos --input_dir=example \\
    >     --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \\
    >     --name=a --mode=h
    >
    > cms sbatch generate slurm.in.sh \\
    >    --config=a.py,b.json,c.yaml \\
    >    --attributes=a=1,b=4 \\
    >    --noos \\
    >    --input_dir=example \\
    >    --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \\
    >    --name=a \\
    >    --mode=h
    >
    > cms sbatch generate slurm.in.sh \\
    >    --verbose \\
    >    --config=a.py,b.json,c.yaml \\
    >    --attributes=name=gregor,a=1,b=4 \\
    >    --noos \\
    >    --input_dir=example \\
    >    --experiment="epoch=[1-3] x=[1,4] y=[10,11]" \\
    >    --mode=f \\
    >    --name=a
    >
    > cms sbatch generate slurm.in.sh --experiments-file=experiments.yaml --name=a
    >
    > cms sbatch generate submit --name=a


