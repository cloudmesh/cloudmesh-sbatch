"""
API to create multiple batch scripts based on parameters you specify.

The parameters are permutated on and for each a specific batch script
is created. The batch scripts are placed either in a directory hierarchy,
or in the same directory.

The API is also accessible through a commandline interface and both are
aligned in functionality with each other.

The command line interface is documented at ... TODO: autogeneate with cms man

The logic is documented at TODO: create a manual

A video about this effort is located at TODO: locate video, post to gregor as mp4 so he can edit with macOS

sbatch reads in a template slurm script that is augmented with {variables}. These {variables}
will be replaced from a dictionary.
"""
import itertools
import json
import os
import pathlib
import textwrap
import typing
from collections import OrderedDict
from datetime import datetime
from pprint import pprint

import yaml

from cloudmesh.common.FlatDict import FlatDict
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner
from cloudmesh.common.util import readfile, writefile

PathLike = typing.Union[str, pathlib.Path]
DictOrList = typing.Union[dict, list]
OptPath = typing.Optional[PathLike]
OptStr = typing.Optional[str]


class SBatch:

    def __init__(self, mode: str = "flat", verbose: bool = False):
        """

        Args:
            mode (str): if specified as flat the batch scripts are written in a single directory. Otherwise
                        hierarchical directories are created that include each the batch scripts. When
                        the scripts are executed. The outputs are written into that directory.
            verbose (bool): If True some debug information is written while using it.
        """
        self.name: OptStr = None
        self.data: dict = dict()
        self.verbose: bool = verbose
        self.source: OptPath = None
        self.script_out: OptPath = None
        self.out_directory: OptPath = "."
        self.attributes: dict[str, str] = dict()
        self.dryrun: bool = True
        self.execution_mode: str = mode
        self.permutations: list[typing.Any] = list()
        self.configuration_parameters = None
        self.template_path = None
        self.template_content = None

    def cli_builder(self, arguments: typing.Any):
        """Configures the object from command.sbatch CLI arguments

        TODO: arguments is typically a dict or a dotdict. Why is this typing.Any?

        TODO: what is Fluent ?

        Args:
            arguments: The docopts object from the cms sbatch command.

        Returns:
            Fluent API of the current object.
        """
        self.source = arguments.get('SOURCE', self.source)
        self.dryrun = arguments.get('dryrun', self.dryrun)
        if self.execution_mode is not None and arguments.execution_mode != 'debug':
            self.execution_mode = arguments['mode']

        if self.script_out is None and arguments.out is None:
            self.script_out = self.source.replace(".in.", ".").replace(".in", "")
        else:
            self.script_out = arguments.get('out', self.script_out)

        if arguments['--dir']:
            self.out_directory = arguments['--dir']

        if not arguments["--noos"]:
            self.update_from_os_environ()

        if arguments.attributes:
            self.attributes = self.update_from_attribute_str(arguments.attributes)

        for configfile in Parameter.expand(arguments.config):
            self.update_from_file(configfile)
        return self

    def register_script(self, script):
        """Registers and reads the template script in for processing.

        This method must be run at least once prior to generating the slurm script output.

        Args:
            script (string): A string that is the path to the template script.

        Returns:
            The text of the template file unaltered.
        """
        self.template_path = script
        self.template_content = readfile(script)
        return self.template_content

    def from_yaml(self, yaml_file: PathLike):
        """Configures the object from a standard YAML structure.

        TODO: what is fluent?

        Args:
            yaml_file (string or path): The path to the yaml file to parse

        Returns:
            Fluent API of the current object.

        The yaml file supports the following YAML structure::

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
        """

        def _apply_leaf(my_dict: DictOrList, my_lambda: typing.Callable, *args, **kwargs) -> dict:
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
                    new_dict[key] = _apply_leaf(value, my_lambda, *args, **kwargs)
                elif isinstance(value, list):
                    inner_list = list()
                    for x in value:
                        if isinstance(x, dict) or isinstance(x, list):
                            inner_list.append(_apply_leaf(x, my_lambda, *args, **kwargs))
                        else:
                            inner_list.append(my_lambda(x, **kwargs))
                        new_dict[key] = inner_list
                else:
                    new_dict[key] = my_lambda(str(value), *args, **kwargs)
            return new_dict

        with open(yaml_file, 'rb') as f:
            yaml_data = yaml.safe_load(f)

        if 'template' in yaml_data:
            self.register_script(yaml_data['template'])
        if 'config' in yaml_data:
            self.update_from_file(yaml_data['config'])
        self.name = yaml_data.get('name', self.name)
        self.execution_mode = yaml_data.get('mode', self.execution_mode)
        if 'dir' in yaml_data:
            self.out_directory = yaml_data['dir']
        if 'experiments' in yaml_data:
            experiments = _apply_leaf(yaml_data['experiments'], Parameter.expand)
            perms = self.permutation_generator(experiments)
            self.permutations = self.permutations + perms
        if 'attributes' in yaml_data:
            self.attributes.update(yaml_data['attributes'])

        return self

    @staticmethod
    def permutation_generator(exp_dict: dict) -> list:
        """Creates a cartisian product of a {key: list, ...} object.

        Args:
            exp_dict: The dictionary to process

        Returns:
            A list of dictionaries containing the resulting cartisian product.

        For example::

            my_dict = {"key1": ["value1", "value2"], "key2": ["value3", "value4"]}
            out = permutation_generator(my_dict)
            out # [{"key1": "value1", "key2": 'value3"},
                #  {"key1": "value1", "key2": "value4"},
                #  {"key1": "value2", "key2": "value3"},
                #  {"key1": "value2", "key2": "value4"}

        """
        keys, values = zip(*exp_dict.items())
        return [dict(zip(keys, value)) for value in itertools.product(*values)]

    def set_attribute(self, attribute: str, value: typing.Any):
        self.data[attribute] = value
        return self

    def update_from_dict(self, d: typing.Any):
        self.data.update(d)
        return self

    def update_from_attribute_str(self, attributes: str) -> dict:
        """attributes are of the form "a=1,b=3"

        TODO: this function seems to be a duplicate from a feature included in cloudmesh.common.Parameter

        Args:
            attributes: a Parameterized string of the form "a=1,b=2"

        Returns:
            A dict with the parameters

        """
        entries = Parameter.arguments_to_dict(attributes)
        self.data.update(entries)
        return entries

    def update_from_os_environ(self, load: bool = True) -> dict:
        """Updates the config file output to include OS environment variables

        Args:
            load: When true, loads the environment variables into the config.

        Returns:
            The current value of the data file.
        """
        if load:
            self.data.update(dict(os.environ))
        return self.data

    @staticmethod
    def _suffix(path: PathLike) -> str:
        """
        returns the suffix of a filename

        Args:
            path (path or string):

        Returns:
            The suffx of the filename

        """
        return pathlib.Path(path).suffix

    def update_from_file(self, filename: PathLike) -> dict:
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
            values = dict(FlatDict(json.loads(content), sep="."))
            self.data.update(values)
        elif suffix.lower() in [".yaml", ".yml"]:
            content = readfile(filename)
            values = dict(FlatDict(yaml.safe_load(content), sep="."))
            self.data.update(values)
        elif suffix.lower() in [".py"]:
            Console.error("# ERROR: Importing python not yet implemented")
        elif suffix.lower() in [".ipynb"]:
            Console.error("# ERROR: Importing jupyter notebooks not yet implemented")
        return self.data

    def generate(self, script: str = None, data: dict = None, fences=("{", "}")) -> str:
        """Expands the script template given the passed configuration.

        Args:
            script: The string contents of the script file.
            data: A single-level dictionary used to replace strings that match the key with its values.
            fences: A 2 position tuple, that encloses template variables (start and end).

        Returns:
            The script that has expanded its values based on `data`.
        """
        if data is None:
            data = self.attributes
        if script is None:
            script = self.template_content
        content = script
        for attribute, value in data.items():
            if self.verbose:
                print(f"Expanding {fences[0] + attribute + fences[1]} with {value}")
            frame = fences[0] + attribute + fences[1]
            if frame in content:
                content = content.replace(frame, str(value))
        return content

    def generate_experiment_permutations(self, variable_str: str) -> list[typing.Any]:
        """Generates experiment permutations based on the passed string and appends it to the current instance.

        Args:
            variable_str: A Parameter.expand string (such as epoch=[1-3] x=[1,4] y=[10,11])

        Returns:
            list with permutations over the experiment variables
        """
        experiments = OrderedDict()
        my_params = Parameter.arguments_to_dict(variable_str)

        for k, v in my_params:
            experiments[k] = Parameter.expand(v)
        self.permutations.append(self.permutation_generator(experiments))
        return self.permutations

    @staticmethod
    def _bootstrap_generator(permutation):
        values = list()
        for attribute, value in permutation.items():
            values.append(f"{attribute}_{value}")
        assignments = list()
        for attribute, value in permutation.items():
            assignments.append(f"{attribute}={value}")
        assignments = " ".join(assignments)

        identifier = "_".join(values)
        return identifier, assignments, values

    def _generate_flat(self):
        """Runs process to build out all templates in a flat-style

        Returns:
            None.

        Side Effects:
            Writes two files for each established experiment.
        """
        configuration = dict()
        suffix = self._suffix(self.script_out)
        name = self.script_out.replace(suffix, "")
        directory = self.out_directory

        for permutation in self.permutations:
            identifier, assignments, values = self._bootstrap_generator(permutation)
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

        self.configuration_parameters = configuration
        print(Printer.write(configuration, order=["id", "experiment", "script", "config"]))
        self.generate_setup_from_configuration(configuration)

        Console.error("script generation nott yet implemented")

    def _generate_hierarchical(self):
        """Runs process to build out all templates in a hierarchical-style

        Returns:
            None.

        Side Effects:
            Writes two files for each established experiment, each in their own directory.
        """
        configuration = dict()
        suffix = self._suffix(self.script_out)
        name = self.script_out.replace(suffix, "")
        directory = self.out_directory
        for permutation in self.permutations:
            identifier, assignments, values = self._bootstrap_generator(permutation)
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

        banner("Script generation")

        print(Printer.write(configuration, order=["id", "experiment", "script", "config", "directory"]))

        self.configuration_parameters = configuration
        self.generate_setup_from_configuration(configuration)

        Console.error("script generation ont yet implemented")

    def generate_experiment_slurm_scripts(self, mode: str = None):
        """Utility method to genrerate either hierarchical or flat outputs; or debug.

        Args:
            mode: The mode of operation.  One of: "debug", "flat", "hierarchical"

        Returns:

        """
        mode = mode if mode else self.execution_mode
        if mode in ["debug", "d"]:
            for permutation in self.permutations:
                values = ""
                for attribute, value in permutation.items():
                    values = values + f"{attribute}={value} "
                    script = f"{self.out_directory}/{self.script_out}{values}".replace("=", "_")
                print(f"{values} sbatch {self.script_out} {script}")
        elif mode.startswith("f"):
            self._generate_flat()
        elif mode.startswith("h"):
            self._generate_hierarchical()

    def generate_submit(self, name: PathLike = None):
        """
        Generates the slurm submit script based on parameters set.

        Args:
            name (str): name of the configuration file

        Returns:

        """
        experiments = self.configuration_parameters = json.loads(readfile(name))

        if experiments is None:
            Console.error("please define the experiment parameters")
            return ""

        for entry in experiments:
            experiment = experiments[entry]
            parameters = experiment["experiment"]
            directory = experiment["directory"]
            script = os.path.basename(experiment["script"])
            print(f"{parameters} sbatch -D {directory} {script}")

    def generate_setup_from_configuration(self, configuration: dict):
        """
        TODO: ...

        Args:
            configuration (dict):

        Returns:

        """
        pprint(configuration)
        for identifier in configuration:
            Console.info(f"setup experiment {identifier}")
            experiment = configuration[identifier]
            Shell.mkdir(experiment["directory"])

            # Generate config.yml
            Console.info(f"* write file {experiment['config']}")

            writefile(experiment["config"], yaml.dump(experiment["variables"], indent=2))
            content_config = readfile(experiment["config"])
            try:
                check = yaml.safe_load(content_config)
            except Exception as e:
                print(e)
                Console.error("We had issues with our check for the config.yaml file")

            # Generate slurm.sh
            content_script = readfile(self.source)
            content_script = self.generate(content_script, experiment["variables"])
            writefile(experiment["script"], content_script)

    @property
    def now(self) -> str:
        """
        The current time in format "%Y-m-%d"

        Returns:
             time in format "%Y-m-%d"

        """
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
        {key}===END===
            """)

    def save_experiment_configuration(self, name: str = None):
        """
        Writes the experminent configuration to a file

        Args:
            name (str): The path representing the filename location

        Returns:

        """
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
