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
# from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.variables import Variables

class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        """
        ::

          Usage:
                sbatch generate submit [--verbose] --name=NAME
                sbatch generate [--verbose] [--mode=MODE] [--config=CONFIG...] [--attributes=PARAMS] [--out=DESTINATION] [--gpu=GPU] SOURCE [--dryrun] [--noos] [--dir=DIR] [--experiment=EXPERIMENT] --name=NAME
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
              --attributes=PARAMS       TBD
              --out=DESTINATION         TBD
              --gpu=GPU                 TBD
              --noos                    TBD
              --experiment=EXPERIMENT   TBD
              --account=ACCOUNT         TBD
              --mode=MODE               one of "flat", "debug", "hierachical" can als just use "f". "d", "h" [default: debug]
              --name=NAME               name of the experiment configuration file

          Description:

               > Example:
               > cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" --name=a
               > cms sbatch generate slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" --name=a
               > cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=name=gregor,a=1,b=4 --dryrun --noos --dir=example --experiment="epoch=[1-3] x=[1,4] y=[10,11]" --mode=f --name=a

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
                       "name"
                       )

        # VERBOSE(arguments)

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


        if arguments.generate and arguments.submit:

            # sbatch generate submit [--verbose] [--mode=MODE] [--experiment=EXPERIMENT] [--dir=DIR]

            sbatch = SBatch()
            sbatch.verbose = arguments.verbose

            sbatch.generate_submit(name=arguments.name)

            return ""

        elif arguments.generate:

            sbatch = SBatch()

            sbatch.source = arguments.SOURCE

            if arguments.out is None:
                sbatch.destination = sbatch.source.replace(".in.", ".").replace(".in", "")
            else:
                sbatch.destination = arguments.out
            if sbatch.source == sbatch.destination:
                if not yn_choice("The source and destination filenames are the same. Do you want to continue?"):
                    return ""

            sbatch.attributes = arguments.gpu
            sbatch.directory = arguments["--dir"]
            sbatch.dryrun = arguments.dryrun
            sbatch.config = (arguments.config[0]).split(",") # not soo good to split. maybe Parameter expand is better

            experiment = arguments.experiment

            experiments = None

            if not arguments["--noos"]:
                sbatch.update_from_os_environ()

            if sbatch.directory is not None:
                sbatch.source = f"{sbatch.directory}/{sbatch.source}"
                sbatch.destination = f"{sbatch.directory}/{sbatch.destination}"

            if arguments.attributes:
                sbatch.attributes = sbatch.update_from_attribute_str(arguments.attributes)

            if arguments.experiment:
                permutations = sbatch.generate_experiment_permutations(arguments.experiment)

            if verbose:
                print(f"Experiments:  {arguments.experiment}")
                sbatch.info()
                print()

            for configfile in sbatch.config:
                if sbatch.directory is not None:
                    configfile = f"{sbatch.directory}/{configfile}"
                sbatch.update_from_file(configfile)

            content = readfile(sbatch.source)

            if sbatch.dryrun or verbose:
                banner("Attributes")
                pprint (sbatch.data)
                banner(f"Original Script {sbatch.source}")
                print(content)
                banner("end script")
            result = sbatch.generate(content)

            if sbatch.dryrun or verbose:
                banner("Script")
                print (result)
                banner("Script End")
            else:
                writefile(sbatch.destination, result)

            sbatch.generate_experiment_slurm_scripts(mode=arguments.mode)

            sbatch.save_experiment_configuration(name=arguments.name)
            # print(get_attribute_parameters(arguments.attributes))

        return ""
