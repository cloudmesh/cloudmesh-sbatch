from pprint import pprint

from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile
from cloudmesh.common.util import writefile
from cloudmesh.common.util import yn_choice
from cloudmesh.sbatch.sbatch import SBatch
from cloudmesh.sbatch.slurm import Slurm
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.variables import Variables
from cloudmesh.common.parameter import Parameter


class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        """::

          Usage:
                sbatch generate submit --name=NAME [--type=JOB_TYPE] [--verbose]
                sbatch generate SOURCE --name=NAME [--verbose] [--mode=MODE] [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT]
                sbatch generate --setup=FILE [SOURCE] [--verbose] [--mode=MODE]  [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT] [--name=NAME]
                sbatch slurm start
                sbatch slurm stop
                sbatch slurm info

          sbatch allows the creation of parameterized batch
          scripts. The initioal support includes slurm, but we intend
          also to support LSF. Parameters can be specified on the
          commandline or in configuration files. Configuration files
          can be formulated as json,yaml, python, or jupyter
          notebooks.

          Parameters defined in this file arethen used in the slur
          batc script and substituted with their values. A special
          parameter called experiment defines a number of variables
          thet are permuted on when used allowing mutliple batch
          scripts to be defined easily to conduct parameter studies.

          Please note that the setup flag is deprecated and is in
          future versions fully covered while just using the config
          file.

          Arguments:
              FILENAME       name of a slurm script generated with sbatch
              CONFIG_FILE    yaml file with configuration
              ACCOUNT        account name for host system
              SOURCE         name for slurm script
              PARAMS         parameter lists for experimentation
              GPU            name of gpu

          Options:
              -h                        help
              --dryrun                  flag to do a dryrun and not create files and directories (not tested)
              --config=CONFIG...        a list of comma seperated configuration files in yaml or json format. The endings must be .json or .yaml
              --setup=FILE              TBD
              --type=JOB_TYPE           The method to generate submission scripts.  One of slurm, lsf. [default: slurm]
              --attributes=PARAMS       a list of coma separated attribute value pars to set parameters that are used.
              --out=DESTINATION         TBD
              --account=ACCOUNT         TBD
              --gpu=GPU                 The name of the GPU. Tyoically k80, v100, a100, rtx3090, rtx3080
              --noos                    ignores environment variable substitution from the shell. This can be helpfull when debugging as the list is quite lareg
              --nocm                    cloudmesh as a variable dictionary build in. Any vaiable refered to by cloudmes. and its name is replaced from the
                                        cloudmesh variables
              --experiment=EXPERIMENT   This specifies all parameters that are used to create permutations of them. They are comma separated key value pairs
              --mode=MODE               one of "flat", "debug", "hierachical" can also just use "f". "d", "h" [default: debug]
              --name=NAME               name of the experiment configuration file

          Description:

               > Examples:
               >
               > cms sbatch generate slurm.in.sh --verbose \
               >     --config=a.py,b.json,c.yaml \
               >     --attributes=a=1,b=4 \
               >     --dryrun --noos --dir=example \
               >     --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \
               >     --name=a --mode=h

               > cms sbatch generate slurm.in.sh \
               >    --config=a.py,b.json,c.yaml \
               >    --attributes=a=1,b=4  \
               >    --noos \
               >    --dir=example \
               >    --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \
               >    --name=a \
               >    --mode=h\

               > cms sbatch generate slurm.in.sh \
               >    --verbose \
               >    --config=a.py,b.json,c.yaml \
               >    --attributes=name=gregor,a=1,b=4 \
               >    --noos \
               >    --dir=example \
               >    --experiment="epoch=[1-3] x=[1,4] y=[10,11]" \
               >    --mode=f \
               >    --name=a

               > cms sbatch generate slurm.in.sh --experiments-file=experiments.yaml --name=a

               > cms sbatch generate submit --name=a

        """
        arguments.verbose = arguments["--verbose"]

        map_parameters(arguments,
                       "account",
                       "filename",
                       "attributes",
                       "gpu",
                       "dryrun",
                       "config",
                       "out",
                       "experiment",
                       "mode",
                       "name")

        # pprint(args)
        # pprint(arguments)

        # arguments["experiments_file"] = arguments["--experiments-file"]

        #
        # UNDO GREGORS CHANGES
        #
        #if arguments.config:
        #    try:
        #        arguments.config = Parameter.expand(arguments.config[0])
        #    except Exception as e:
        #        Console.error("issue with config expansion")
        #        print(e)
        #
        ### Handling in sbatch class now
        # if arguments.attributes:
        #     arguments.attributes = Parameter.arguments_to_dict(arguments.attributes)
        # if arguments.config:
        #     arguments.config = Parameter.expand(arguments.config[0])

        verbose = arguments["--verbose"]
        if verbose:
            banner("experiment batch generator")

        if arguments.slurm:
            if arguments.start:
                Slurm.start()
            elif arguments.stop:
                Slurm.stop()
            elif arguments.info:
                Slurm.status()

            return ""

        if arguments.name is not None:
            if not arguments.name.endswith(".json"):
                arguments.name = arguments.name + ".json"

        VERBOSE(arguments)

        if arguments.generate and arguments.submit:

            # sbatch generate submit [--verbose] [--mode=MODE] [--experiment=EXPERIMENT] [--dir=DIR]

            sbatch = SBatch()
            sbatch.verbose = arguments.verbose
            if '--type' not in arguments or arguments['--type'] is None:
                type_ = "slurm"
            else:
                type_ = arguments['--type']
            sbatch.generate_submit(name=arguments.name, type_=type_)

            return ""

        elif arguments.generate:

            sbatch = SBatch()

            if arguments.get('--setup') is not None:
                sbatch.config_from_yaml(arguments["--setup"])

            # CLI arguments override the experiments
            sbatch.config_from_cli(arguments)

            # sbatch.mode = arguments.mode
            # content = readfile(sbatch.source)

            if sbatch.dryrun or verbose:
                banner("Configuration")
                print(sbatch.debug_state(key=".."))
                print()
                banner(f"Original Script {sbatch.source}")
                print(sbatch.template_content)
                banner("end script")
            result = sbatch.generate(sbatch.template_content)

            if sbatch.dryrun or verbose:
                banner("Expanded Script")
                print(result)
                banner("Script End")
            else:
                writefile(sbatch.script_out, result)

            sbatch.generate_experiment_slurm_scripts()

            sbatch.save_experiment_configuration(name=arguments.name)

        return ""
