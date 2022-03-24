import os
import sys
import yaml
import textwrap
import subprocess
from cloudmesh.common.util import readfile, writefile, path_expand
from cloudmesh.common.util import yn_choice
from cloudmesh.common.Shell import Shell
from pprint import pprint
import pathlib
from cloudmesh.common.console import Console
from cloudmesh.common.FlatDict import FlatDict
import json
from cloudmesh.common.util import banner
from cloudmesh.common.parameter import Parameter
from collections import OrderedDict
import itertools
import textwrap


class SBatch:

    def __init__(self, verbose=False):
        banner("init")
        self.data = {}
        self.template = None
        self.verbose = verbose
        self.gpu = None
        print(self.data)

    def info(self):
        for a in ["source",
                    "destination",
                    "attributes",
                    "gpu",
                    "dryrun",
                    "config",
                    "directory",
                    "experiment",
                    "permutations"
                          ]:
            print(f'{a:<12}: {self.data.get(a)}')

        print()

    def set_attribute(self, attribute, value):
        self.data[attribute] = value

    def update_from_dict(self, d):
        self.data.update(d)

    def update_from_attribute_str(self, attributes):
        """
        attributes are of the form "a=1,b=3"

        :param attributes:
        :type attributes:
        :return:
        :rtype:
        """
        attributes = attributes.split(",")
        entries = {}
        for attribute in attributes:
            name, value = attribute.split('=')
            entries[name] = value
        self.data.update(entries)
        return entries

    def update_from_os_environ(self, load=True):
        if load:
            self.data.update(dict(os.environ))
        return self.data

    def _suffix(self, path):
        return pathlib.Path(path).suffix

    def update_from_file(self, filename):
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = self._suffix(filename)
        content = readfile(filename)

        if suffix.lower() in [".json"]:
            values = dict(FlatDict(json.loads(content), sep="."))
            self.data.update(values)
        elif suffix.lower() in [".yaml"]:
            content = readfile(filename)
            values = dict(FlatDict(yaml.safe_load(content), sep="."))
            self.data.update(values)
        elif suffix.lower() in [".py"]:
            Console.red("# ERROR: Importing python not yet implemented")
        elif suffix.lower() in [".ipynb"]:
            Console.red("# ERROR: Importing jupyter notebooks not yet implemented")
        return self.data

    def generate(self, script):
        self.content = self.script = script
        for attribute, value in self.data.items():
            frame = "{" + attribute + "}"
            if frame in self.content:
                self.content = self.content.replace(frame, value)
        return self.content

    def generate_experiment_permutations(self, variable_str):
        """
        creates permutations over the variable use dto define an experiment parameter sweep

        :param variable_str: epoch=[1-3] x=[1,4] y=[10,11]
        :type variable_str: str
        :return: list with permutations over the experiment variables
        :rtype: dict of strings
        """
        experiments = OrderedDict()
        permutations = []
        entries = variable_str.split(' ')

        for entry in entries:
            name, parameters = entry.split('=')
            experiments[name] = Parameter.expand(parameters)
        keys, values = zip(*experiments.items())
        self.permutations = [dict(zip(keys, value)) for value in itertools.product(*values)]
        return self.permutations

    #for permutation in self.permutations:
    #    values = ""
    #    for attribute, value in permutation.items():
    #        values = values + f"{attribute}={value} "
    #        script = f"{self.destination}{values}".replace("=", "_")
    #    print(f"{values} sbatch {self.destination} {script}")

    def generate_experiment_slurm_scripts(self, mode="flat"):
        mode = mode.lower()
        print ("MMM", mode)
        if mode in ["debug", "d"]:
            for permutation in self.permutations:
                values = ""
                for attribute, value in permutation.items():
                    values = values + f"{attribute}={value} "
                    script = f"{self.destination}{values}".replace("=", "_")
                print(f"{values} sbatch {self.destination} {script}")
        elif mode in ["flat", "f"]:
            configs = []
            scripts = []
            suffix = self._suffix(self.destination)
            name = self.destination.replace(suffix, "")
            directory = os.path.dirname(name)
            for permutation in self.permutations:
                values = []
                for attribute, value in permutation.items():
                    values.append(f"{attribute}_{value}")
                identifier = "_".join(values)
                print(identifier)
                script = f"{name}_{identifier}{suffix}"
                scripts.append(script)
                config = f"{directory}/config_{identifier}.yaml"
                configs.append(config)

            banner("Script generation")

            pprint(scripts)
            print()

            pprint(configs)
            print()

            if not yn_choice("The listed scripts will be gnerated, Continue"):
                return


            #
            # now generate the scripts
            #
            Console.error("script generation ont yet implemented")

        elif mode.startswith("hi") or mode in ["hierachy", "hierahical", "h"]:
            Console.error("Mode hierachy not yet implemented")


    @property
    def now(self):
        # there is a better way ;)
        return Shell.run("date").strip().replace(" ", "-")

    def __str__(self):
        return self.content

    def save_slurm_script(self, filename):
        """
        Writes the custom slurm script to a file for submission
        If the file already exists, the user will be prompted to override
        """
        if os.path.exists(path_expand(filename)):
            if yn_choice(f"{filename} exists, would you like to overwrite?"):
                writefile(filename, self.content)
        else:
            writefile(filename, self.content)

    '''
    def run(self, filename='submit-job.slurm'):
        """
        Execute a custom slurm script to the cluster
        """
        cwd = os.getcwd()
        file_path = os.path.join(cwd, filename)
        self.configure_sbatch(host='rivanna')
        if self.params:
            self.get_parameters()
        self.data.update(self.env)
        self.save(file_path)
        if not self.dryrun:
            stdout, stderr = subprocess.Popen(['sbatch', file_path], env=self.env, encoding='utf-8',
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            print(stdout)
            print(f"{stderr = }", file=sys.stderr)
            Shell.run(f'rm {file_path}')
    '''
