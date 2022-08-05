import itertools
import json
import os
import pathlib
import tempfile
import textwrap
import typing
import yaml
import uuid

from collections import OrderedDict
from datetime import datetime
from pprint import pprint

from nbconvert.exporters import PythonExporter

from cloudmesh.common.FlatDict import FlatDict
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner, readfile, writefile, yn_choice
from cloudmesh.common.variables import Variables

PathLike = typing.Union[str, pathlib.Path]
DictOrList = typing.Union[dict, list]
OptPath = typing.Optional[PathLike]
OptStr = typing.Optional[str]


class SBatch:

    def __init__(self, verbose=False):
        self.name = None
        self.data = dict()
        self.permutations = list()
        self.template = None
        self.verbose = verbose
        # self.gpu = None
        self.attributes = dict()
        self.configuration_parameters = None
        self.template_path = None
        self.template_content = None
        self.out_directory = None
        self.script_out = None
        self.execution_mode = None
        self.source = None
        self.dryrun = None

    def config_from_cli(self, arguments: typing.Any):
        """Configures the object from command.sbatch CLI arguments

        Args:
            arguments: The docopts object from the cms sbatch command.

        Returns:
            Fluent API of the current object.
        """
        if arguments.get('SOURCE') is not None:
            self.source = arguments.get('SOURCE')
            self.register_script(self.source)
        self.dryrun = arguments.get('dryrun', self.dryrun)
        if self.execution_mode is None:
            self.execution_mode = arguments.mode

        if self.script_out is None and arguments.out is None:
            self.script_out = pathlib.Path(self.source).name.replace(".in.", ".")  #.replace(".in", "")
        else:
            self.script_out = pathlib.Path(arguments.get('out', self.script_out)).name

        if self.source == self.script_out:
            if not yn_choice("The source and destination filenames are the same. Do you want to continue?"):
                return ""

        if arguments['--dir']:
            self.out_directory = arguments['--dir']

        if not arguments["--noos"]:
            self.update_from_os_environ()

        if not arguments["--nocm"]:
            self.update_from_cm_variables()

        if arguments.attributes:
            self.update_from_attributes(arguments.attributes)

        if arguments.experiment:
            self.permutations = self.generate_experiment_permutations(arguments.experiment)

        if arguments.config:
            for config_file in Parameter.expand(arguments.config):
                self.update_from_file(config_file)
            self.update_from_dict({ 'meta.parent.uuid': str(uuid.uuid4()) })
        return self

    @classmethod
    def _apply_leaf(cls, my_dict: DictOrList, my_lambda: typing.Callable, *args, **kwargs) -> dict:
        """Walks python dictionary and applies a lambda to all leaf nodes.
        Args:
            my_dict: The dictionary to process
            my_lambda: The lambda function to apply to the leaf nodes.
            *args: positional arguments passed directly to my_lambda
            **kwargs: keyword arguments passed directoy to my_lambda
        Returns:
            A new dictionary that has applied the my_lambda function on
            each leaf node.
        """
        new_dict = dict(my_dict)
        for key, value in new_dict.items():
            if isinstance(value, dict):
                new_dict[key] = cls._apply_leaf(value, my_lambda, *args, **kwargs)
            elif isinstance(value, list):
                inner_list = list()
                for x in value:
                    if isinstance(x, dict) or isinstance(x, list):
                        inner_list.append(cls._apply_leaf(x, my_lambda, *args, **kwargs))
                    else:
                        inner_list.append(my_lambda(x, **kwargs))
                    new_dict[key] = inner_list
            else:
                new_dict[key] = my_lambda(str(value), *args, **kwargs)
        return new_dict

    def config_from_yaml(self, yaml_file: PathLike):
        """Configures the object from a standard YAML structure.

        This supports the following YAML structures:
            template: path
            config: path
            name: str
            experiments:
              card_name: Parameter.expand string
              gpu_count: Parameter.expand string
              cpu_num: Parameter.expand string
              mem: Parameter.expand string
            attributes:
              property: substitution
            mode: str
            dir: path

        Args:
            yaml_file: The path to the yaml file to parse

        Returns:
            Fluent API of the current object.
        """

        with open(yaml_file, 'rb') as f:
            yaml_data = yaml.safe_load(f)

        self.read_config_from_dict(yaml_data)

        return self

    def read_config_from_dict(self, root):
        if 'template' in root:
            self.source = root['template']
            self.register_script(root['template'])
        if 'config' in root:
            self.update_from_file(root['config'])
        if 'name' in root:
            self.name = root['name']
        if 'mode' in root:
            self.execution_mode = root['mode']
        if 'dir' in root:
            self.out_directory = root['dir']
        if 'experiments' in root:
            experiments = self._apply_leaf(root['experiments'], Parameter.expand)
            perms = self.permutation_generator(experiments)
            self.permutations = self.permutations + perms
        # if 'attributes' in root:
        self.update_from_dict(FlatDict(root, sep="."))
        self.update_from_dict({ 'meta.parent.uuid': str(uuid.uuid4()) })

    def register_script(self, script):
        """Registers and reads the template script in for processing

        This method must be run at least once prior to generating the slurm script output.

        Args:
            script: A string that is the path to the template script.

        Returns:
            The text of the template file unaltered.
        """
        self.template_path = script
        self.template_content = readfile(script)
        return self.template_content

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
        result = getattr(self, "permutations")
        # pprint(result)
        print()

    def set_attribute(self, attribute, value):
        self.data[attribute] = value

    def update_from_dict(self, d):
        self.data.update(d)

    def update_from_attributes(self, attributes: str):
        """attributes are of the form "a=1,b=3"

        Args:
            attributes: A string to expand into key-value pairs
        Returns:
            dict[str,str]: The expanded dictionary
        """
        entries = Parameter.arguments_to_dict(attributes)
        self.update_from_dict(entries)
        return entries

    def update_from_os_environ(self, load=True):
        """Updates the config file output to include OS environment variables
        Args:
            load: When true, loads the environment variables into the config.
        Returns:
            The current value of the data configuration variable
        """
        if load:
            self.update_from_dict(dict(os.environ))
        return self.data

    def update_from_cm_variables(self, load: bool = True) -> typing.Dict[str, typing.Any]:
        """Adds Cloudmesh variables to the class's data parameter as a flat dict.

        Args:
            load: Toggles execution; if false, method does nothing.

        Returns:
            The updated data parameter with the cloudmesh variables set.
        """
        if load:
            variables = Variables()
            v = FlatDict({"cloudmesh": variables.dict()}, sep=".")

            self.update_from_dict(dict(v))
        return self.data

    @staticmethod
    def _suffix(path: str) -> str:
        """Returns the file suffix of a path

        Args:
            path: The path to process

        Returns:
            str: The suffix of the string
        """
        return pathlib.Path(path).suffix

    def update_from_file(self, filename: PathLike):
        """Updates the run configuration file with the data within the passed file.

        Args:
            filename: The path to the configuration file (json or yaml)

        Returns:
            The modified data object.
        """
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = self._suffix(filename)
        content = readfile(filename)

        if suffix.lower() in [".json"]:
            regular_dict = json.loads(content)
            values = dict(FlatDict(regular_dict, sep="."))
        elif suffix.lower() in [".yml", ".yaml"]:
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
            # regular_dict = None
            # values = None

            py_name = filename.replace(".ipynb", ".py")
            jupy = PythonExporter()
            body, _ = jupy.from_filename(filename)
            writefile(py_name, body)
            # Shell.run(f"jupyter nbconvert --to python {filename}")

            filename = py_name
            modulename = filename.replace(".py","").replace("/","_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            regular_dict = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    print(name, value)
                    regular_dict[name] = value

            values = dict(FlatDict(regular_dict, sep="."))
        else:
            raise RuntimeError(f"Unsupported config type {suffix}")

        self.read_config_from_dict(regular_dict)
        if regular_dict is not None and 'experiments' in regular_dict:
            exp_values = regular_dict['experiments']

            banner(str(exp_values))

            if isinstance(exp_values, dict):
                entries = []
                for key, value in exp_values.items():
                    entry = f"{key}={value}"
                    entries.append(entry)
                exp_values = " ".join(entries)

            elif isinstance(exp_values, str):
                banner(f"Generate permutations from experiment in {filename}")
            else:
                Console.error(f"experiment datatype {type(exp_values)} for {exp_values} not supported")
            experiments = self._apply_leaf(regular_dict['experiments'], Parameter.expand)
            perms = self.permutation_generator(experiments)
            self.permutations = self.permutations + perms
            # self.generate_experiment_permutations(experiments)

        # if values is not None:
        #     self.update_from_dict(experiments)

        return self.data

    def generate(self, script, data=None, fences=("{", "}")):
        """Expands the script template given the passed configuration.

        Args:
            script: The string contents of the script file.
            data: A single-level dictionary used to replace strings that match the key with its values.
            fences: A 2 position tuple, that encloses template variables (start and end).

        Returns:
            The script that has expanded its values based on `data`.
        """
        if data is None:
            data = self.data
        content = self.template_content
        for attribute, value in data.items():
            frame = fences[0] + attribute + fences[1]
            if self.verbose:
                print(f"Expanding {frame} with {value}")
            # print(content)
            if frame in content:
                content = content.replace(frame, str(value))
        return content

    @staticmethod
    def permutation_generator(exp_dict: dict) -> list:
        """Creates a cartisian product of a {key: list, ...} object.

        Args:
            exp_dict: The dictionary to process

        Returns:
            A list of dictionaries containing the resulting cartisian product.

        For example
            my_dict = {"key1": ["value1", "value2"], "key2": ["value3", "value4"]}
            out = permutation_generator(my_dict)
            out # [{"key1": "value1", "key2": 'value3"},
                #  {"key1": "value1", "key2": "value4"},
                #  {"key1": "value2", "key2": "value3"},
                #  {"key1": "value2", "key2": "value4"}
        """
        keys, values = zip(*exp_dict.items())
        return [dict(zip(keys, value)) for value in itertools.product(*values)]

    def generate_experiment_permutations(self, variable_str):
        """Generates experiment permutations based on the passed string and appends it to the current instance.

        Args:
            variable_str: A Parameter.expand string (such as epoch=[1-3] x=[1,4] y=[10,11])

        Returns:
            list with permutations over the experiment variables
        """
        experiments = OrderedDict()
        entries = variable_str.split(' ')

        # pprint(entries)
        for entry in entries:
            k, v = entry.split("=")
            experiments[k] = Parameter.expand(v)
        self.permutations = self.permutation_generator(experiments)
        return self.permutations

    #for permutation in self.permutations:
    #    values = ""
    #    for attribute, value in permutation.items():
    #        values = values + f"{attribute}={value} "
    #        script = f"{self.destination}{values}".replace("=", "_")
    #    print(f"{values} sbatch {self.destination} {script}")

    @staticmethod
    def _generate_bootstrapping(permutation):
        values = list()
        for attribute, value in permutation.items():
            values.append(f"{attribute}_{value}")
        assignments = list()
        for attribute, value in permutation.items():
            assignments.append(f"{attribute}={value}")
        assignments = " ".join(assignments)

        identifier = "_".join(values)
        return identifier, assignments, values

    def _generate_flat_config(self):

        configuration = dict()
        # self.script_variables = list()
        suffix = self._suffix(self.script_out)
        name = self.script_out.replace(suffix, "")
        # directory = os.path.dirname(name)
        directory = self.out_directory
        for permutation in self.permutations:
            identifier, assignments, values = self._generate_bootstrapping(permutation)
            print(identifier)
            script = f"{directory}/{name}_{identifier}{suffix}"
            config = f"{directory}/config_{identifier}.yaml"
            variables = dict(self.data)
            variables.update(FlatDict({'experiments': permutation}, sep="."))

            configuration[identifier] = {
                "id"        : identifier,
                "directory" : directory,
                "experiment": assignments,
                "script"    : script,
                "config"    : config,
                "variables" : variables
            }
        return configuration

    def _generate_hierarchical_config(self):
        """Runs process to build out all templates in a hierarchical-style

        Returns:
            None.

        Side Effects:
            Writes two files for each established experiment, each in their own directory.

        """
        print("Outputting Hierarchical Experiments")
        configuration = dict()
        self.script_variables = []
        suffix = self._suffix(self.script_out)
        # name = self.script_out.replace(suffix, "")
        directory = self.out_directory  # .path.dirname(name)
        for permutation in self.permutations:
            identifier, assignments, values = self._generate_bootstrapping(permutation)
            print(identifier)
            script = f"{directory}/{identifier}/slurm.sh"
            config = f"{directory}/{identifier}/config.yaml"
            variables = dict(self.data)
            variables.update(FlatDict({'experiments': permutation}, sep="."))

            configuration[identifier] = {
                "id"        : identifier,
                "directory" : f"{directory}/{identifier}",
                "experiment": assignments,
                "script"    : script,
                "config"    : config,
                "variables" : variables
            }
            # pprint(configuration)
        return configuration

    def generate_experiment_slurm_scripts(self, out_mode=None):
        """Utility method to genrerate either hierarchical or flat outputs; or debug.

        Args:
            mode: The mode of operation.  One of: "debug", "flat", "hierarchical"

        Returns:

        """
        mode = self.execution_mode if out_mode is None else out_mode.lower()
        if mode.startswith("d"):
            Console.warning("This is just debug mode")
            print()
            for permutation in self.permutations:
                values = ""
                for attribute, value in permutation.items():
                    values = values + f"{attribute}={value} "
                script = f"{self.out_directory}/{self.script_out}{values}".replace("=", "_")
        else:
            if mode.startswith("f"):
                configuration = self._generate_flat_config()
            elif mode.startswith("h"):
                configuration = self._generate_hierarchical_config()
            else:
                raise RuntimeError(f"Invalid generator mode {mode}")

            banner("Script generation")
            print(Printer.write(configuration, order=["id", "experiment", "script", "config", "directory"]))

            self.configuration_parameters = configuration
            self.generate_setup_from_configuration(configuration)

    def generate_submit(self, name=None, type_='slurm'):
        if type_ == 'slurm':
            cmd = 'sbatch'
        elif type_ == 'lsf':
            cmd = 'bsub'
        else:
            raise RuntimeError(f"Unsupported submission type {type_}")

        experiments = json.loads(readfile(name))

        if experiments is None:
            Console.error("please define the experiment parameters")
            return ""

        for entry in experiments:
            experiment = experiments[entry]
            parameters = experiment["experiment"]
            directory = experiment["directory"]
            script = os.path.basename(experiment["script"])
            print(f"( {parameters} cd {directory} && {cmd} {script} )")

    def generate_setup_from_configuration(self, configuration):
        # pprint(configuration)
        for identifier in configuration:
            perm_uuid = str(uuid.uuid4())
            Console.info(f"setup experiment {identifier}")
            experiment = configuration[identifier]
            Shell.mkdir(experiment["directory"])
            print(f"Making dir {experiment['directory']}")
            #
            # Generate config.yml
            #
            Console.info(f"* write file {experiment['config']}")

            # Generate UUID for each perm
            experiment["variables"].update({ 'meta.uuid': perm_uuid })
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
            writefile(experiment["script"], content_script)

    @property
    def now(self):
        return datetime.now().strftime("%Y-m-%d")

    def debug_state(self, key=""):
        """Outputs the current state of persistent values in class.
        Args:
            key: A string to prefix the string with.
        Returns:
            A mutliline string with all class variables in a key = value pattern.
        """
        return textwrap.dedent(f"""
        {key}===OBJ===
        {key}   {self.name = }
        {key}   {self.data = }
        {key}   {self.verbose = }
        {key}   {self.source = }
        {key}   {self.script_out = }
        {key}   {self.out_directory = }
        {key}   {self.attributes = }
        {key}   {self.dryrun = }
        {key}   {self.execution_mode = }
        {key}   {self.permutations = }
        {key}   {self.configuration_parameters = }
        {key}   {self.template_path = }
        {key}===END===""")

    # def __str__(self):
    #     return self.content
    #
    # def save_slurm_script(self, filename):
    #     """
    #     Writes the custom slurm script to a file for submission
    #     If the file already exists, the user will be prompted to override
    #     """
    #     if os.path.exists(path_expand(filename)):
    #         if yn_choice(f"{filename} exists, would you like to overwrite?"):
    #             writefile(filename, self.content)
    #     else:
    #         writefile(filename, self.content)

    def save_experiment_configuration(self, name=None):
        if name is not None:
            content = json.dumps(self.configuration_parameters, indent=2)
            writefile(name, content)
