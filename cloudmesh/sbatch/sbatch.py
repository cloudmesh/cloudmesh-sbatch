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

from cloudmesh.common.debug import VERBOSE

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


    def __init__(self, verbose=False):
        # self.name = None
        self.flat = FlatDict({}, sep=".")
        self.data = dict()
        self.permutations = list()
        self.experiments = None
        self.dryrun = False
        self.verbose = False
        self.execution_mode = "h"
        self.input_dir = str(Shell.map_filename(".").path)
        self.output_dir = str(Shell.map_filename(".").path)
        self.os_variables = None


        # self.template = None
        # self.verbose = verbose
        # # self.gpu = None
        # self.attributes = dict()
        # self.configuration_parameters = None
        # self.template_path = None
        # self.template_content = None
        # self.out_directory = None
        self.script_out = None
        # self.execution_mode = None
        # self.source = None
        # self.dryrun = None
        pass

    def info(self):
        for a in [
            "dryrun",
            "verbose",
            "name",
            "source",
            "destination",
            "attributes",
            "gpu",
            "config",
            "config_files",
            "directory",
            "experiment",
            "execution_mode",
            "template",
            "script_output",
            "output_dir",
            "input_dir",
            "script_in",
            "script_out",
            "os_variables",
            "experiments"
        ]:
            try:
                result = getattr(self, a)
            except:
                result = self.data.get(a)
            print(f'{a:<12}: {result}')
        print("permutations:")

        result = getattr(self, "permutations")
        pprint(result)

        print ("BEGIN FLAT")
        pprint(self.flat)
        print("END FLAT")
        print()

        print ("BEGIN DATA")
        pprint(self.data)
        print("END DATA")
        print()

        print ("BEGIN YAML")
        spec = yaml.dump(self.data, indent=2)
        print(spec)
        print ("END YAML")

        print("BEGIN SPEC")
        spec = self.spec_replace(spec)
        print (spec)
        print("END SPEC")
        print("BEGIN PERMUTATION")
        p = self.permutations
        pprint (p)
        print("END PERMUTATION")

        # self.info()
        #
        # self.data = result
        #
        print("BEGIN DATA")
        pprint (self.data)
        print("END DATA")

        banner("BEGIN TEMPLATE")
        print(self.template_content)
        banner("END TEMPLATE")

    @staticmethod
    def update_with_directory(directory, filename):
        """
        prefix with the directory if the filename is not starting with . / ~

        :param directory:
        :type directory:
        :param filename:
        :type filename:
        :return:
        :rtype:
        """
        if directory is None:
            return filename
        elif not filename.startswith("/") and not filename.startswith(".") and not filename.startswith("~"):
            return f"{directory}/{filename}"
        else:
            return filename

    # def config_from_cli(self, arguments):
    #     """Configures the object from command.sbatch CLI arguments
    #
    #     Args:
    #         arguments: The docopts object from the cms sbatch command.
    #
    #     Returns:
    #         Fluent API of the current object.
    #     """
    #
    #     VERBOSE(arguments)
    #
    #     # sbatch
    #     # generate
    #     # SOURCE - -name = NAME[--verbose][--mode = MODE] [--config = CONFIG] [--attributes = PARAMS] [
    #     #     --output_dir = DESTINATION] [--dryrun][--noos][--nocm][--input_dir = SOURCE] [--experiment = EXPERIMENT]
    #     print(type(arguments))
    #
    #     # self.source = arguments.source
    #     self.dryrun = arguments.dryrun or False
    #     self.verbose = arguments.verbose
    #     self.execution_mode = arguments.mode
    #     self.name = arguments.name
    #     self.source = arguments.source
    #     self.input_dir = str(Shell.map_filename(arguments["source_dir"]).path)
    #     self.output_dir = str(Shell.map_filename(arguments["output_dir"]).path)
    #     self.script_in = f"{self.input_dir}/{self.source}"
    #     self.os_variables = (arguments.os).split(",")
    #
    #
    #     #
    #     # prepare the output script name
    #     #
    #     # ok
    #     if self.script_out is None and arguments.out is None:
    #         self.script_out = pathlib.Path(self.source).name.replace(".in.", ".")  # .replace(".in", "")
    #     else:
    #         self.script_out = pathlib.Path(arguments.get('out', self.script_out)).name
    #     self.script_out = SBatch.update_with_directory(self.output_dir, self.script_out)
    #
    #     # ok create list of config files
    #     try:
    #         self.config_files = arguments.config.split(",")
    #         self.config_files = [SBatch.update_with_directory(self.input_dir, filename) for filename in self.config_files]
    #     except Exception as e:
    #         print (e)
    #
    #     # ok
    #     self.source = SBatch.update_with_directory(self.input_dir, self.source)
    #
    #     # ok
    #     if self.source == self.script_out:
    #         Console.error("The source and destination filenames are the same.", traceflag=True)
    #         return ""
    #
    #     # ok
    #     self.load_source_template(self.source)
    #
    #     # ok
    #     if not arguments["--noos"]:
    #         self.update_from_os_environ()
    #
    #     # ok
    #     if not arguments["--nocm"]:
    #         self.update_from_cm_variables()
    #
    #     # ok
    #     try:
    #         self.attributes = arguments.attributes
    #     except:
    #         pass
    #
    #     # ok
    #     if arguments.attributes:
    #         self.update_from_attributes(arguments.attributes)
    #
    #
    #     self.info()
    #
    #     # order of replace is defined by
    #     # config
    #     # os
    #     # cm
    #     # attributes
    #
    #
    #     # ok
    #     if arguments.config:
    #         for config_file in self.config_files:
    #             self.update_from_file(config_file)
    #         # elf.update_from_dict({ 'meta.parent.uuid': str(uuid.uuid4()) })
    #
    #     self.update_from_os(self.os_variables)
    #     d = self.get_data(flat=False)
    #
    #
    #     #ok
    #     if arguments.experiment:
    #         self.experiments = arguments.experiment
    #         self.experiment = self.generate_experiment_permutations(self.experiments)
    #     else:
    #         self.experiments = d.get("experiment", None)
    #     result = self.get_data(flat=arguments.flat)
    #
    #     experiments = result["experiment"]
    #     for e in experiments:
    #         experiments[e] = Parameter.expand(experiments[e])
    #
    #     self.permutations = self.permutation_generator(experiments)
    #
    #     return result
    #
    # def yaml(self):
    #     spec = yaml.dump(self.data, indent=2)


    def get_data(self, flat=False):
        result = self.data

        if flat:
            from cloudmesh.common.FlatDict import FlatDict
            result = FlatDict(self.data, sep=".")
            del result["sep"]

        return result


    def spec_replace(self, spec):
        import re
        import munch
        variables = re.findall(r"\{\w.+\}", spec)

        for i in range(0, len(variables)):
            data = yaml.load(spec, Loader=yaml.SafeLoader)

            m = munch.DefaultMunch.fromDict(data)

            for variable in variables:
                text = variable
                variable = variable[1:-1]
                try:
                    value = eval("m.{variable}".format(**locals()))
                    if "{" not in value:
                        spec = spec.replace(text, value)
                except:
                    value = variable
        return spec

    def update_from_os(self, variables):
        if variables is not None:
            if os not in self.data:
                self.data["os"] = {}
            for key in variables:
                self.data["os"][key] = os.environ[key]
        return self.data

    def load_source_template(self, script):
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

    def update_from_dict(self, d):
        self.data.update(d)
        return self.data

    def update_from_attributes(self, attributes: str):
        """attributes are of the form "a=1,b=3"

        Args:
            attributes: A string to expand into key-value pairs
        Returns:
            dict[str,str]: The expanded dictionary
        """
        flatdict = Parameter.arguments_to_dict(attributes)

        d = FlatDict(flatdict, sep=".")
        d = d.unflatten()
        del d["sep"]

        self.update_from_dict(d)
        return self.data

    def update_from_os_environ(self):
        """Updates the config file output to include OS environment variables
        Args:
            load: When true, loads the environment variables into the config.
        Returns:
            The current value of the data configuration variable
        """
        self.update_from_dict(dict(os.environ))
        return self.data

    def update_from_cm_variables(self, load=True):
        """Adds Cloudmesh variables to the class's data parameter as a flat dict.

        Args:
            load: Toggles execution; if false, method does nothing.

        Returns:
            The updated data parameter with the cloudmesh variables set.
        """
        if load:
            variables = Variables()
            v = FlatDict({"cloudmesh": variables.dict()}, sep=".")
            d = v.unflatten()
            del d["sep"]
            self.update_from_dict(d)
        return self.data

    @staticmethod
    def _suffix(path):
        """Returns the file suffix of a path

        Args:
            path: The path to process

        Returns:
            str: The suffix of the string
        """
        return pathlib.Path(path).suffix

    def update_from_file(self, filename):
        """Updates the run configuration file with the data within the passed file.

        Args:
            filename: The path to the configuration file (json or yaml)

        Returns:
            The modified data object.
        """
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = self._suffix(filename).lower()
        content = readfile(filename)

        if suffix in [".json"]:
            values = json.loads(content)
            # values = dict(FlatDict(regular_dict, sep="."))

        elif suffix in [".yml", ".yaml"]:
            content = readfile(filename)
            values = yaml.safe_load(content)
            # values = dict(FlatDict(regular_dict, sep="."))

        elif suffix in [".py"]:

            modulename = filename.replace(".py", "").replace("/", "_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            values = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    print(name, value)
                    values[name] = value
            # values = dict(FlatDict(regular_dict, sep="."))

        elif suffix in [".ipynb"]:
            # regular_dict = None
            # values = None

            py_name = filename.replace(".ipynb", ".py")
            jupy = PythonExporter()
            body, _ = jupy.from_filename(filename)
            writefile(py_name, body)
            # Shell.run(f"jupyter nbconvert --to python {filename}")

            filename = py_name
            modulename = filename.replace(".py", "").replace("/", "_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            values = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    print(name, value)
                    values[name] = value


            # values = dict(FlatDict(regular_dict, sep="."))
        else:
            raise RuntimeError(f"Unsupported config type {suffix}")

        self.update_from_dict(values)


        # self.read_config_from_dict(regular_dict)
        if values is not None and 'experiment' in values:
            experiments = values['experiment']

            for key, value in experiments.items():
                experiments[key] = Parameter.expand(value)

            self.permutations = self.permutation_generator(experiments)

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
    def permutation_generator(exp_dict):
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

    # for permutation in self.permutations:
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
                "id": identifier,
                "directory": directory,
                "experiment": assignments,
                "script": script,
                "config": config,
                "variables": variables
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
                "id": identifier,
                "directory": f"{directory}/{identifier}",
                "experiment": assignments,
                "script": script,
                "config": config,
                "variables": variables
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

    def generate_submit(self, name=None, job_type='slurm'):
        if job_type == 'slurm':
            cmd = 'sbatch'
        elif job_type == 'lsf':
            cmd = 'bsub'
        else:
            cmd = job_type

        # else:
        #    raise RuntimeError(f"Unsupported submission type {type_}")

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
            experiment["variables"].update({'meta.uuid': perm_uuid})
            writefile(experiment["config"], yaml.dump(experiment["variables"], indent=2))
            content_config = readfile(experiment["config"])
            try:
                check = yaml.safe_load(content_config)
            except Exception as e:
                print(e)
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
