from pprint import pprint

import docopt
import sys

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
        """
        ::

          Usage:
                sbatch generate submit [--verbose] --name=NAME
                sbatch generate SOURCE [--verbose] [--mode=MODE] [--setup=FILE] [--config=CONFIG] [--attributes=PARAMS] [--out=DESTINATION] [--dryrun] [--noos] [--nocm] [--dir=DIR] [--experiment=EXPERIMENT] --name=NAME
                sbatch slurm start
                sbatch slurm stop
                sbatch slurm info

          This command does some useful things.

          Arguments:
              FILENAME       name of a slurm script generated with sbatch
              CONFIG_FILE    yaml file with configuration
              ACCOUNT        account name for host system
              SOURCE         name for slurm script
              PARAMS         parameter lists for experimentation
              GPU            name of gpu

          Options:
              -h                        help
              --dryrun                  flag to skip submission
              --config=CONFIG...        TBD
              --setup=FILE              TBD
              --attributes=PARAMS       TBD
              --out=DESTINATION         TBD
              --noos                    TBD
              --nocm                    TBD
              --experiment=EXPERIMENT   TBD
              --account=ACCOUNT         TBD
              --mode=MODE               one of "flat", "debug", "hierachical" can als just use "f". "d", "h" [default: debug]
              --name=NAME               name of the experiment configuration file

          Description:

               > Example:
               > cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" --name=a --mode=h
               > cms sbatch generate slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" --name=a --mode=h
               > cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=name=gregor,a=1,b=4 --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]" --mode=f --name=a
               > cms sbatch generate slurm.in.sh --experiments-file=experiments.yaml --name=a

               > cms sbatch generate submit --name=a

        """
        verbose = arguments["--verbose"]

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

            sbatch.generate_submit(name=arguments.name)

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
                banner("Attributes")
                pprint (sbatch.data)
                banner(f"Original Script {sbatch.source}")
                print(sbatch.template_content)
                banner("end script")
            result = sbatch.generate(sbatch.template_content)

            if verbose:
                print(f"Experiments:  {arguments.experiment}")
                sbatch.info()
                print()

            if sbatch.dryrun or verbose:
                banner("Script")
                print(result)
                banner("Script End")
            else:
                writefile(sbatch.script_out, result)

            sbatch.generate_experiment_slurm_scripts(mode=arguments.mode)

            sbatch.save_experiment_configuration(name=arguments.name)

        return ""
