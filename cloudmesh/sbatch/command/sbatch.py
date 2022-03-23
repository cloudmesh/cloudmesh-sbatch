#from cloudmesh.sbatch.api.manager import Manager
import os
import configparser
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


class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        """
        ::

          Usage:
                sbatch [--verbose] [--config=CONFIG...] [--attributes=PARAMS] [--out=DESTINATION] [--gpu=GPU] SOURCE [--dryrun] [--noos] [--dir=DIR] [--experiment=EXPERIMENT] [--account=ACCOUNT]
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
               > cms sbatch two slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a:1,b:4 --dryrun --noos --dir=example
               > cms sbatch slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
               > cms sbatch slurm.in.sh --config=a.py,b.json,c.yaml --attributes=a=1,b=4  --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\"
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
                banner("Begin SLURM startup)")
                os.system("sudo systemctl start slurmctld")
                os.system("sudo systemctl start slurmd")
                os.system("sudo scontrol update nodename=white state=idle")
                banner("sinfo")
                os.system("sinfo")
                banner("squeue")
                os.system("squeue")
                banner ("End of SLURM startup ")
                return ""
            elif arguments.stop:
                os.system("sudo systemctl stop slurmd")
                os.system("sudo systemctl stop slurmctld")
                return ""
            elif arguments.info:
                for command in ["sudo tail /var/log/slurm-llnl/slurmd.log",
                                "sudo tail /var/log/slurm-llnl/slurmctld.log",
                                "sinfo -R"]:
                    banner(command)
                    os.system(command)

            return ""

        source = arguments.SOURCE
        if arguments.out is None:
            destination = source.replace(".in.", ".").replace(".in", "")
        else:
            destination = arguments.out
        if source == destination:
            if not yn_choice("The source and destination filenames are the same. Do you want to continue?"):
                return ""

        account = arguments.account
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
            print (f"Source:      {source}")
            print (f"Destination: {destination}")
            print(f"Attributes:   {attributes}")
            print (f"GPU:         {gpu}")
            print(f"Dryrun:       {dryrun}")
            print(f"Config:       {config}")
            print(f"Directory:    {directory}")
            print(f"Experiments:  {experiment}")
            print("Permutations")
            pprint(permutations)
            print()

        mod = {}

        for configfile in config:
            if directory is not None:
                configfile = f"{directory}/{configfile}"
            if ".py" in configfile:
                if verbose:
                    print(f"Reading variables from {configfile}")
                Console.red("# ERROR: Importing python not yet implemented")
                continue
            elif ".json" in configfile:
                if verbose:
                    print(f"Reading variables from {configfile}")
                content = readfile(configfile)
                values =  dict(FlatDict(json.loads(content), sep="__"))
                data.update(values)

            elif ".yaml" in configfile:
                if verbose:
                    print(f"Reading variables from {configfile}")
                content = readfile(configfile)
                values = dict(FlatDict(yaml.safe_load(content), sep="__"))
                data.update(values)
            content = readfile(source)
            if dryrun or verbose:
                banner("Attributes")
                pprint (data)
                banner(f"Original Script {source}")
                print(content)
                banner("end script")

            if account is None:
                if 'user__account' in data.keys():
                    account = data['user__account']
                else:
                    Console.red("# ERROR: Account is either unavailable or not defined")
            if 'user__runpath' in data.keys():
                sbatch_runpath = data['user__runpath']
            else:
                Console.red("# ERROR: Must define a directory for the runpath")

            if dryrun or verbose:
                banner("Script")
                print (result)
                banner("Script End")

            destination_temp = destination.replace(".slurm","-")
            for permutation in permutations:
                values = ""
                for attribute,value in permutation.items():
                    values = values + f"{attribute}={value}-"
                    if f"model_parameters__{attribute}" in data.keys():
                        data[f"model_parameters__{attribute}"] = value
                values = values[:-1]
                path = f"{destination_temp}{values}".replace("=","_")+".slurm"
                job_directory = path.replace(".slurm","")
                if directory is not None:
                    sbatch_directory = job_directory.split("/")[-1]
                    script = path.split("/")[-1]
                else:
                    sbatch_directory = job_directory
                    script = path
                #TODO clean up these paths used above
                cluster_directory = os.path.join(sbatch_runpath,os.environ['USER'],sbatch_directory)
                user_directory = os.path.join(sbatch_runpath, os.environ['USER'])
                if not os.path.exists(cluster_directory):
                    if not os.path.exists(user_directory):
                        if not os.path.exists(sbatch_runpath):
                            os.mkdir(sbatch_runpath)
                        os.mkdir(user_directory)
                    os.mkdir(cluster_directory)
                with open(os.path.join(cluster_directory,"config.json"),"w") as outfile:
                    json.dump(data, outfile, indent=2)
                result = content.replace("SBATCH_RUNSTAMP",sbatch_directory)
                result = result.replace("SBATCH_RUNPATH",sbatch_runpath)
                writefile(os.path.join(cluster_directory,script), result)
                cluster_directory = os.path.abspath(cluster_directory)
                if account is not None:
                    if arguments.gpu:
                        for gpu in Parameter.expand_string(arguments.gpu):
                            worker = SBatch(path=cluster_directory,
                                            account=arguments.account,
                                            gpu=gpu,
                                            dryrun=arguments.dryrun)
                            worker.run(arguments.filename)
                    else:
                        worker = SBatch(path=cluster_directory,
                                        account=arguments.account,
                                        dryrun=arguments.dryrun)
                        worker.run(arguments.filename)

                else:
                    Console.red("# ERROR: Account is either unavailable or not defined")

            # print(get_attribute_parameters(arguments.attributes))

            return ""
