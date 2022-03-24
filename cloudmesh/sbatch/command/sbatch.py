#from cloudmesh.sbatch.api.manager import Manager
import os
from cloudmesh.common.console import Console
from cloudmesh.common.util import path_expand
from pprint import pprint
from cloudmesh.common.debug import VERBOSE
from cloudmesh.shell.command import map_parameters
from cloudmesh.sbatch.sbatch import SBatch
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.common.parameter import Parameter
import itertools
from cloudmesh.common.util import banner
from cloudmesh.common.util import yn_choice
from cloudmesh.common.util import readfile
from cloudmesh.common.util import writefile
from cloudmesh.common.FlatDict import FlatDict
from cloudmesh.sbatch.slurm import Slurm

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

        #if arguments.old:

        #    if not arguments.filename:
        #        arguments.filename = 'submit-job.slurm'

        #    if arguments.gpu:
        #        for gpu in Parameter.expand_string(arguments.gpu):
        #            if arguments.attributes:
        #                params = dict()
        #                for attribute in arguments.attributes.split(';'):
        #                    name, feature = attribute.split('=')
        #                    params[f'{name}'] = Parameter.expand(feature)
        #                keys, values = zip(*params.items())
        #                permutations = [dict(zip(keys, value)) for value in itertools.product(*values)]
        #                for params in permutations:
        #                    worker = SBatch(slurm_config, arguments.account, params=params, dryrun=arguments.dryrun)
        #                    worker.run(arguments.filename)
        #    else:
        #        worker = SBatch(slurm_config, arguments.account, dryrun=arguments.dryrun)
        #        worker.run(arguments.filename)

        #else:

        if verbose:
            banner("experiment batch generator")

        from pprint import pprint
        import json
        import yaml


        if arguments.slurm:
            if arguments.start:
                Slurm.start()
            elif arguments.stop:
                Slurm.stop()
            elif arguments.info:
                Slurm.status()

            return ""


        sbatch = SBatch()

        source = arguments.SOURCE
        if arguments.out is None:
            destination = source.replace(".in.", ".").replace(".in", "")
        else:
            destination = arguments.out
        if source == destination:
            if not yn_choice("The source and destination filenames are the same. Do you want to continue?"):
                return ""

        gpu = arguments.gpu
        directory = arguments.dir
        dryrun = arguments.dryrun
        config = (arguments.config[0]).split(",") # not soo good to split. maybe Parameter expand is better

        experiment = arguments.experiment

        experiments = None


        if not arguments["--noos"]:
            sbatch.update_from_os_environ()

        if directory is not None:
            source = f"{directory}/{source}"
            destination = f"{directory}/{destination}"

        if arguments.attributes:
            attributes = sbatch.update_from_attribute_str(arguments.attributes)

        from collections import OrderedDict
        if arguments.experiment:
            experiments = OrderedDict()
            permutations = []
            entries = experiment.split(' ')

            for entry in entries:
                name, parameters = entry.split('=')
                experiments[name] = Parameter.expand(parameters)
            keys, values = zip(*experiments.items())
            permutations = [dict(zip(keys, value)) for value in itertools.product(*values)]
            if verbose:
                pprint (permutations)

        if verbose:
            print(f"Source:       {source}")
            print(f"Destination:  {destination}")
            print(f"Attributes:   {attributes}")
            print(f"GPU:          {gpu}")
            print(f"Dryrun:       {dryrun}")
            print(f"Config:       {config}")
            print(f"Directory:    {directory}")
            print(f"Experiments:  {experiment}")
            print("Permutations")
            pprint(permutations)
            print()
            sbatch.info()


        mod = {}

        for configfile in config:
            if directory is not None:
                configfile = f"{directory}/{configfile}"
            data = sbatch.update_from_file(configfile)

        content = readfile(source)

        if dryrun or verbose:
            banner("Attributes")
            pprint (sbatch.data)
            banner(f"Original Script {source}")
            print(content)
            banner("end script")
        result = sbatch.generate(content)

        if dryrun or verbose:
            banner("Script")
            print (result)
            banner("Script End")
        else:
            writefile(destination, result)

        for permutation in permutations:
            values = ""
            for attribute,value in permutation.items():
                values = values + f"{attribute}={value} "
                script = f"{destination}{values}".replace("=","_")
            print (f"{values} sbatch {destination} {script}")


        # print(get_attribute_parameters(arguments.attributes))

        return ""
