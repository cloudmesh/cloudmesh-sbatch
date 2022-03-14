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

class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        """
        ::

          Usage:
                sbatch --slurm_config=CONFIG_FILE --account=ACCOUNT [--filename=FILENAME] [--attributes=PARAMS] [--gpu=GPU] [--dryrun]

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

        """
        map_parameters(arguments,
                       "slurm_config",
                       "account",
                       "filename",
                       "attributes",
                       "gpu",
                       "dryrun")

        try:
            os.path.exists(path_expand(arguments.slurm_config))
            slurm_config = arguments.slurm_config
        except Exception as e:
            print('slurm_template path does not exist')

        if not arguments.filename:
            arguments.filename = 'submit-job.slurm'

        if arguments.gpu:
            for gpu in Parameter.expand_string(arguments.gpu):
                if arguments.attributes:
                    params = dict()
                    for attribute in arguments.attributes.split(';'):
                        name, feature = attribute.split('=')
                        params[f'{name}'] = Parameter.expand(feature)
                    keys, values = zip(*params.items())
                    permutations = [dict(zip(keys, value)) for value in itertools.product(*values)]
                    for params in permutations:
                        worker = SBatch(slurm_config, arguments.account, params=params, dryrun=arguments.dryrun)
                        worker.run(arguments.filename)
        else:
            worker = SBatch(slurm_config, arguments.account, dryrun=arguments.dryrun)
            worker.run(arguments.filename)

        return ""
