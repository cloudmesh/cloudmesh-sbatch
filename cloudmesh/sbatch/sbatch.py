import itertools
import json
import os
import pathlib
from collections import OrderedDict
from pprint import pprint

import yaml

from cloudmesh.common.FlatDict import FlatDict
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile, writefile, path_expand
from cloudmesh.common.util import yn_choice
from cloudmesh.common.variables import Variables


class SBatch:

    def __init__(self, verbose=False):
        self.data = {}
        self.template = None
        self.verbose = verbose
        self.gpu = None
        self.configuration_parameters = None

    def info(self):
        for a in ["source",
                    "destination",
                    "attributes",
                    "gpu",
                    "dryrun",
                    "config",
                    "directory",
                    "experiment",
                    "mode"
                  ]:
            try:
                result = getattr(self,a)
            except:
                result = self.data.get(a)
            print(f'{a:<12}: {result}')
        print("permutations:")
        result = getattr(self,"permutations")
        pprint(result)
        print()

    def set_attribute(self, attribute, value):
        self.data[attribute] = value

    def update_from_dict(self, d):
        self.data.update(d)

    def update_from_attributes(self, attributes):
        """
        attributes are of the form "a=1,b=3"

        :param attributes:
        :type attributes:
        :return:
        :rtype:
        """
        # replace the next lines with
        # entries = Parameter.arguments_to_dict(attributes)
        # start delete
        self.data.update(attributes)
        return attributes

    def update_from_os_environ(self, load=True):
        if load:
            self.data.update(dict(os.environ))
        return self.data

    def update_from_cm_variables(self, load=True):
        if load:
            variables = Variables()
            v = FlatDict({"cloudmesh": variables.dict()}, sep=".")

            self.data.update(dict(v))
        return self.data

    def _suffix(self, path):
        return pathlib.Path(path).suffix

    def update_from_file(self, filename):
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = self._suffix(filename)
        content = readfile(filename)

        if suffix.lower() in [".json"]:
            regular_dict = json.loads(content)
            values = dict(FlatDict(regular_dict, sep="."))
        elif suffix.lower() in [".yaml"]:
            content = readfile(filename)
            regular_dict = yaml.safe_load(content)
            values = dict(FlatDict(regular_dict, sep="."))
        elif suffix.lower() in [".py"]:

            modulename = filename.replace(".py","").replace("/","_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            regular_dict = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    print (name, value)
                    regular_dict[name] = value
            values = dict(FlatDict(regular_dict, sep="."))

        elif suffix.lower() in [".ipynb"]:
            regular_dict = None
            values = None
            Console.red("# ERROR: Importing jupyter notebooks not yet implemented")

        if regular_dict is not None and  'experiment' in regular_dict:
            exp_values = regular_dict['experiment']

            banner(str(exp_values))

            if type(exp_values) == dict:

                entries = []
                for key,value in exp_values.items():
                    entry = f"{key}={value}"
                    entries.append(entry)
                exp_values = " ".join(entries)


            elif type(exp_values) == str:
                banner(f"Generate permutations from experiment in {filename}")
            else:
                Console.error(f"experiment datatype {type(exp_values)} for {exp_values} not supported")
            self.generate_experiment_permutations(exp_values)

        if values is not None:
            self.data.update(values)

        return self.data

    def generate(self, script, data=None):
        if data is None:
            data = self.data
        content =  script
        for attribute, value in data.items():
            frame = "{" + attribute + "}"
            if frame in content:
                content = content.replace(frame, str(value))
        return content



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
        if mode.startswith("d"):
            Console.warning ("This is just debug mode")
            print()
            for permutation in self.permutations:
                values = ""
                for attribute, value in permutation.items():
                    values = values + f"{attribute}={value} "
                    script = f"{self.destination} {values}".replace("=", "_")
                print(f"{values} sbatch {self.destination} {script}")

        elif mode.startswith("f"):
            print("FFFF")

            configuration = {}
            self.script_variables=[]
            suffix = self._suffix(self.destination)
            name = self.destination.replace(suffix, "")
            directory = os.path.dirname(name)
            for permutation in self.permutations:
                values = []
                for attribute, value in permutation.items():
                    values.append(f"{attribute}_{value}")
                assignments = []
                for attribute, value in permutation.items():
                    assignments.append(f"{attribute}={value}")
                assignments = " ".join(assignments)

                identifier = "_".join(values)
                print(identifier)
                script = f"{name}_{identifier}{suffix}"
                config = f"{directory}/config_{identifier}.yaml"
                variables = self.data
                variables.update(permutation.items())

                configuration[identifier] = {
                    "id": identifier,
                    "directory": directory,
                    "experiment": assignments,
                    "script": script,
                    "config": config,
                    "variables": variables
                }

            banner("Script generation")

            pprint(configuration)
            self.configuration_parameters = configuration
            print (Printer.write(configuration, order=["id", "experiment", "script", "config"]))

            # if not yn_choice("The listed scripts will be gnerated, Continue"):
            #    return

            #
            # now generate the scripts
            #
            self.generate_setup_from_configuration(configuration)

            Console.error("script generation not yet implemented")

        elif mode.startswith("h"):
            print ("HHHH")
            configuration = {}
            self.script_variables = []
            suffix = self._suffix(self.destination)
            name = self.destination.replace(suffix, "")
            directory = os.path.dirname(name)
            for permutation in self.permutations:
                values = []
                for attribute, value in permutation.items():
                    values.append(f"{attribute}_{value}")
                assignments = []
                for attribute, value in permutation.items():
                    assignments.append(f"{attribute}={value}")
                assignments = " ".join(assignments)

                identifier = "_".join(values)
                print(identifier)
                script = f"{directory}/{identifier}/slurm.sh"
                config = f"{directory}/{identifier}/config.yaml"
                variables = dict(self.data)
                variables.update(permutation)

                configuration[identifier] = {
                    "id": identifier,
                    "directory": f"{directory}/{identifier}",
                    "experiment": assignments,
                    "script": script,
                    "config": config,
                    "variables": variables
                }
            else:
                Console.error("No mode specified.")

            banner("Script generation")

            pprint(configuration)

            print(Printer.write(configuration, order=["id", "experiment", "script", "config", "directory"]))

            self.configuration_parameters = configuration
            #if not yn_choice("The listed scripts will be gnerated, Continue"):
            #    return

            #
            # now generate the scripts
            #
            self.generate_setup_from_configuration(configuration)

            Console.error("script generation not yet implemented")

    def generate_submit(self, name=None):
        experiments = self.configuration_parameters = json.loads(readfile(name))

        if experiments is None:
            Console.error ("please define the experiment parameters")
            return ""

        for entry in experiments:
            experiment = experiments[entry]
            parameters = experiment["experiment"]
            directory = experiment["directory"]
            script = os.path.basename(experiment["script"])
            print (f"{parameters} sbatch -D {directory} {script}")

    def generate_setup_from_configuration(self, configuration):
        print ("IIIIIII")
        pprint(configuration)
        for identifier in configuration:
            Console.info(f"setup experiment {identifier}")
            experiment = configuration[identifier]
            Shell.mkdir(experiment["directory"])

            #
            # Generate config.yml
            #
            Console.info(f"* write file {experiment['config']}")

            writefile(experiment["config"], yaml.dump(experiment["variables"], indent=2))
            content_config = readfile(experiment["config"])
            try:
                check = yaml.safe_load(content_config)
            except Exception as e:
                print (e)
                Console.error("We had issues with our check for the config.yaml file")
            #
            # Generate slurm.sh
            #
            content_script = readfile(self.source)
            content_script = self.generate(content_script, experiment["variables"])
            writefile (experiment["script"], content_script)

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

    def save_experiment_configuration(self, name=None):
        if name is not None:
            content = json.dumps(self.configuration_parameters, indent=2)
            writefile(name, content)

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
