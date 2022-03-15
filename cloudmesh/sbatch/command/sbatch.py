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
from cloudmesh.common.FlatDict import FlatDict


class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        """
        ::

          Usage:
                sbatch [--config=CONFIG...] [--attributes=PARAMS] [--out=DESTINATION] [--gpu=GPU] SOURCE [--dryrun] [--noos] [--dir=DIR] [--experiment=EXPERIMENT]

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
               > cms sbatch two slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a:1,b:4 --dryrun --noos --dir=example


        """
        map_parameters(arguments,
                       "slurm_config",
                       "account",
                       "filename",
                       "attributes",
                       "gpu",
                       "dryrun",
                       "config",
                       "out",
                       "dir", "experiment"
                       )

        try:
            os.path.exists(path_expand(arguments.slurm_config))
            slurm_config = arguments.slurm_config
        except Exception as e:
            print('slurm_template path does not exist')

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

        banner("experimental next gen cms sbatch command")

        from pprint import pprint
        import json
        import yaml


        source = arguments.SOURCE
        if arguments.out is None:
            destination = source.replace(".in.", "").replace(".in", "")
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


        if arguments["--noos"]:
            data = {}
        else:
            data = dict(os.environ)


        if directory is not None:
            source = f"{directory}/{source}"
            destination = f"{directory}/{destination}"

        if arguments.attributes:
            entries = {}
            attributes = arguments.attributes
            attributes = attributes.split(",")
            for attribute in arguments.attributes.split(','):
                name, value = attribute.split('=')
                entries[name] = value
            attributes = dict(entries)
            data.update(entries)

        print (f"Source:      {source}")
        print (f"Destination: {destination}")
        print(f"Attributes:   {attributes}")
        print (f"GPU:         {gpu}")
        print(f"Dryrun:       {dryrun}")
        print(f"Config:       {config}")
        print(f"Directory:    {directory}")
        print(f"Experiments:  {experiment}")
        print()


        mod = {}

        for configfile in config:
            if directory is not None:
                configfile = f"{directory}/{configfile}"
            if ".py" in configfile:
                print(f"Reading variables from {configfile}")
                Console.error(" not yet implemented")

            elif ".json" in configfile:

                print(f"Reading variables from {configfile}")
                content = readfile(configfile)
                values =  dict(FlatDict(json.loads(content), sep="__"))
                data.update(values)
                #pprint (data)

                Console.error(" not yet implemented")

            elif ".yaml" in configfile:
                print(f"Reading variables from {configfile}")
                content = readfile(configfile)
                values = dict(FlatDict(yaml.safe_load(content), sep="__"))
                data.update(values)

                Console.error(" not yet implemented")

        content = readfile(source)

        if dryrun:
            banner("Attributes")
            pprint (data)
            banner(f"Original Script {source}")
            print(content)
            banner("end script")
        result = str(content).format(**data)

        if dryrun:
            banner("Script")
            print (result)
            banner("Script End")

        else:
            Console.error("only dryrun is implemented")

        from collections import OrderedDict
        if arguments.experiment:
            experiments = OrderedDict()
            permutations = []
            entries = experiment.split(' ')
            print (entries)

            for entry in entries:
                name, parameters = entry.split('=')
                experiments[name] = Parameter.expand(parameters)
            keys, values = zip(*experiments.items())
            permutations = [dict(zip(keys, value)) for value in itertools.product(*values)]
            pprint (permutations)

        # print(get_attribute_parameters(arguments.attributes))

        return ""
