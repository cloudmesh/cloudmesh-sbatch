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


class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        """
        ::

          Usage:
                sbatch generate [--verbose] [--config=CONFIG...] [--attributes=PARAMS] [--out=DESTINATION] [--gpu=GPU] SOURCE [--dryrun] [--noos] [--dir=DIR] [--experiment=EXPERIMENT]
                sbatch run FILENAME
                sbatch slurm start
                sbatch slurm stop
                sbatch slurm info

          This command does some useful things.

          Arguments:
              CONFIG_FILE    yaml file with configuration
              ACCOUNT        account name for host system
              FILENAME       name for slurm script
              PARAMS         parameter lists for experimentation
              GPU            name of gpu

          Options:
              -h                help
              --dryrun          flag to skip submission

          Description:

               > Example:
               > cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
               > cms sbatch generate slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
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
                       "dir",
                       "experiment"
                       )

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
            sbatch.directory = arguments.dir
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

            for permutation in permutations:
                values = ""
                for attribute,value in permutation.items():
                    values = values + f"{attribute}={value} "
                    script = f"{sbatch.destination}{values}".replace("=","_")
                print (f"{values} sbatch {sbatch.destination} {script}")


            # print(get_attribute_parameters(arguments.attributes))

        return ""
