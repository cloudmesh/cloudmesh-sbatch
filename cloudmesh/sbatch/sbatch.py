import itertools
import json
import os
import pathlib
import typing
import uuid
from collections import OrderedDict
from datetime import datetime
from pprint import pprint

import yaml
from nbconvert.exporters import PythonExporter

from cloudmesh.common.FlatDict import FlatDict
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner, readfile, writefile
from cloudmesh.common.variables import Variables

PathLike = typing.Union[str, pathlib.Path]
DictOrList = typing.Union[dict, list]
OptPath = typing.Optional[PathLike]
OptStr = typing.Optional[str]


class SBatch:

    def __init__(self, verbose=False):
        """
        Initialize the SBatch Object

        :param verbose: If true prints additional infromation when SBatch methods are called
        :type verbose: bool
        """
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
        self.verbose = verbose
        self.template_path = None
        self.template_content = None
        self.configuration_parameters = None
        self.script_out = None
        # self.gpu = None

    def info(self, verbose=None):
        """
        Prints information about the SBatch object for debugging purposes

        :param verbose:  if True prints even more information
        :type verbose: bool
        :return: None
        :rtype: None
        """
        verbose = verbose or self.verbose

        if not verbose:
            return

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
            except:  # noqa: E722
                result = self.data.get(a)
            print(f'{a:<12}: {result}')
        print("permutations:")

        result = getattr(self, "permutations")
        pprint(result)

        print("BEGIN FLAT")
        pprint(self.flat)
        print("END FLAT")
        print()

        print("BEGIN DATA")
        pprint(self.data)
        print("END DATA")
        print()

        print("BEGIN YAML")
        spec = yaml.dump(self.data, indent=2)
        print(spec)
        print("END YAML")

        print("BEGIN SPEC")
        spec = self.spec_replace(spec)
        print(spec)
        print("END SPEC")
        print("BEGIN PERMUTATION")
        p = self.permutations
        pprint(p)
        print("END PERMUTATION")

        # self.info()
        #
        # self.data = result
        #
        print("BEGIN DATA")
        pprint(self.data)
        print("END DATA")

        banner("BEGIN TEMPLATE")
        print(self.template_content)
        banner("END TEMPLATE")

    @staticmethod
    def update_with_directory(directory, filename):
        """
        prefix with the directory if the filename is not starting with . / ~

        :param directory: the string value of the directory
        :type directory: str
        :param filename: the filename
        :type filename: str
        :return: directory/filename
        :rtype: str
        """
        if directory is None:
            return filename
        elif not filename.startswith("/") and not filename.startswith(".") and not filename.startswith("~"):
            return f"{directory}/{filename}"
        else:
            return filename

    def get_data(self, flat=False):
        result = self.data

        if flat:
            from cloudmesh.common.FlatDict import FlatDict
            result = FlatDict(self.data, sep=".")
            del result["sep"]

        return result

    def spec_replace(self, spec):
        """
        given a spec in yaml format, replaces all values in the yaml file taht are of the form "{a.b}"
        with the value of

        a:
           b: value

        if it is defined in the yaml file

        :param spec: yaml string
        :type spec: str
        :return: replaced yaml file
        :rtype: str
        """
        import re
        import munch
        variables = re.findall(r"\{\w.+\}", spec)

        banner("GGGGGGGGGGGGGGGGGGGGGGG")

        data = yaml.load(spec, Loader=yaml.SafeLoader)

        pprint(data)
        banner("RRRRRRRRRRRRRRRRRRRRRRRRR")
        m = munch.DefaultMunch.fromDict(data)

        for i in range(0, len(variables)):

            for variable in variables:
                text = variable
                variable = variable[1:-1]
                try:
                    value = eval("m.{variable}".format(**locals()))
                    if "{" not in value:
                        spec = spec.replace(text, value)
                except:  # noqa: E722
                    value = variable


        banner("UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU")
        pprint(spec)
        return spec

    def update_from_os(self, variables):
        """
        LOads all variables from os.environ into self.data with os.name

        :param variables: tha name of the variables such as "HOME"
        :type variables:  [str]
        :return: self.data with all variaples added with os.name: value
        :rtype: dict
        """
        if variables is not None:
            if os not in self.data:
                self.data["os"] = {}
            for key in variables:
                self.data["os"][key] = os.environ[key]
        return self.data

    def load_source_template(self, script):
        """
        Registers and reads the template script in for processing

        This method must be run at least once prior to generating the batch script output.

        :param script: A string that is the path to the template script.
        :type script: str
        :return: The text of the template file unaltered.
        :rtype: str
        """
        self.template_path = script
        self.template_content = readfile(script)
        return self.template_content

    def update_from_dict(self, d):
        """
        Add a dict to self. data

        :param d: dictionary
        :type d: dict
        :return: self.data with updated dict
        :rtype: dict
        """
        self.data.update(d)
        return self.data

    def update_from_attributes(self, attributes: str):
        """
        attributes are of the form "a=1,b=3"

        :param attributes: A string to expand into key-value pairs
        :type attributes:
        :return: self.data with updated dict
        :rtype: dict
        """
        flatdict = Parameter.arguments_to_dict(attributes)

        d = FlatDict(flatdict, sep=".")
        d = d.unflatten()
        del d["sep"]

        self.update_from_dict(d)
        return self.data

    def update_from_os_environ(self):
        """
        Updates the config file output to include OS environment variables

        :return: The current value of the data configuration variable
        :rtype: dict
        """
        self.update_from_dict(dict(os.environ))
        return self.data

    def update_from_cm_variables(self, load=True):
        """
        Adds Cloudmesh variables to the class's data parameter as a flat dict.

        :param load: Toggles execution; if false, method does nothing.
        :type load: bool
        :return: self.data with updated cloudmesh variables
        :rtype: dict
        """
        if load:
            variables = Variables()
            v = FlatDict({"cloudmesh": variables.dict()}, sep=".")
            d = v.unflatten()
            del d["sep"]
            self.update_from_dict(d)
        return self.data

    @staticmethod
    def _suffix(filename):
        """

        :param filename: Returns the file suffix of a filename
        :type filename: str
        :return: the suffix of the filename
        :rtype: str
        """
        return pathlib.Path(filename).suffix

    def update_from_file(self, filename):
        """
        Updates the configuration self.data with the data within the passed file.

        :param filename: The path to the configuration file (yaml, json, py, ipynb)
        :type filename: str
        :return: self.data with updated cloudmesh variables from the specified file
        :rtype: dict
        """
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = self._suffix(filename).lower()
        content = readfile(filename)

        if suffix in [".json"]:
            values = json.loads(content)

        elif suffix in [".yml", ".yaml"]:
            content = readfile(filename)
            values = yaml.safe_load(content)

        elif suffix in [".py"]:

            modulename = filename.replace(".py", "").replace("/", "_").replace("build_", "")
            from importlib.machinery import SourceFileLoader

            mod = SourceFileLoader(modulename, filename).load_module()

            values = {}
            for name, value in vars(mod).items():
                if not name.startswith("__"):
                    values[name] = value

        elif suffix in [".ipynb"]:

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
                    values[name] = value

        else:
            raise RuntimeError(f"Unsupported config type {suffix}")

        self.update_from_dict(values)

        # self.read_config_from_dict(regular_dict)
        if values is not None and 'experiment' in values:
            experiments = values['experiment']

            for key, value in experiments.items():
                print (key, value)
                try:
                    experiments[key] = Parameter.expand(value)
                except:
                    experiments[key] = [value]

            self.permutations = self.permutation_generator(experiments)

        return self.data

    def generate(self, script=None, variables=None, fences=("{", "}")):
        """
        Expands the script template given the passed configuration.

        :param script: The string contents of the script file.
        :type script: str
        :param variables: the variables to be replaced, if ommitted uses the internal variables found
        :type variables: dict
        :param fences: A 2 position tuple, that encloses template variables (start and end).
        :type fences: (str,str)
        :return: The script that has expanded its values based on `data`.
        :rtype: str
        """

        replaced = {}

        if variables is None:
            variables = self.data
        if script is None:
            script = self.template_content
        content = str(script)
        flat = FlatDict(variables, sep=".")

        for attribute in flat:
            value = flat[attribute]
            frame = fences[0] + attribute + fences[1]
            if frame in content:
                if self.verbose:
                    print(f"- Expanding {frame} with {value}")
                replaced[attribute] = value
                content = content.replace(frame, str(value))
        return content, replaced

    @staticmethod
    def permutation_generator(exp_dict):
        """
        Creates a cartisian product of a {key: list, ...} object.

        :param exp_dict: The dictionary to process
        :type exp_dict: dict
        :return: A list of dictionaries containing the resulting cartisian product.
        :rtype: list

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
        """
        Generates experiment permutations based on the passed string and appends it to the current instance.

        :param variable_str: A Parameter.expand string (such as epoch=[1-3] x=[1,4] y=[10,11])
        :type variable_str: str
        :return: list with permutations over the experiment variables
        :rtype: list
        """
        experiments = OrderedDict()
        entries = variable_str.split(' ')

        for entry in entries:
            k, v = entry.split("=")
            experiments[k] = Parameter.expand(v)
        self.permutations = self.permutation_generator(experiments)
        return self.permutations

    @staticmethod
    def _generate_bootstrapping(permutation):
        """
        creates an identifier, a list of assignments, ad values.

        :param permutation: the permutation list
        :type permutation: list
        :return: identifier, assignments, values
        :rtype: str, list, list
        """
        values = list()
        for attribute, value in permutation.items():
            values.append(f"{attribute}_{value}")
        assignments = list()
        for attribute, value in permutation.items():
            assignments.append(f"{attribute}={value}")
        assignments = " ".join(assignments)

        identifier = "_".join(values)
        return identifier, assignments, values

    # def _generate_flat_config(self):
    #     """
    #     deprecated. IT is no longer supported
    #
    #     Creates a flat configuration file.
    #
    #     :return: dict with information where the variables are a flatdict
    #     :rtype: dict
    #     """
    #
    #     configuration = dict()
    #     # self.script_variables = list()
    #     suffix = self._suffix(self.script_out)
    #     spec = yaml.dump(self.data, indent=2)
    #     spec = self.spec_replace(spec)
    #
    #     directory = self.output_dir
    #     for permutation in self.permutations:
    #         identifier, assignments, values = self._generate_bootstrapping(permutation)
    #
    #         spec = yaml.dump(self.data, indent=2)
    #         spec = self.spec_replace(spec)
    #
    #         variables = yaml.safe_load(spec)
    #
    #         name = os.path.basename(self.script_out)
    #         script = f"{directory}/{name}_{identifier}{suffix}"
    #         config = f"{directory}/config_{identifier}.yaml"
    #
    #         variables.update({'experiment': permutation})
    #         variables["sbatch"]["idenitfier"] = identifier
    #
    #         configuration[identifier] = {
    #             "id": identifier,
    #             "directory": directory,
    #             "experiment": assignments,
    #             "script": script,
    #             "config": config,
    #             "variables": variables
    #         }
    #     return configuration

    def _generate_hierarchical_config(self):
        """
        Creates a hierarchical directory with configuration yaml files, and shell script

        :return: directory with configuration and yaml files
        :rtype: dict
        """
        """Runs process to build out all templates in a hierarchical-style

        Returns:
            None.

        Side Effects:
            Writes two files for each established experiment, each in their own directory.

        """
        if self.verbose:
            print("Outputting Hierarchical Experiments")
        configuration = dict()
        self.script_variables = []
        suffix = self._suffix(self.script_out)
        directory = self.output_dir  # .path.dirname(name)
        for permutation in self.permutations:

            identifier, assignments, values = self._generate_bootstrapping(permutation)

            if self.verbose:
                print(identifier, assignments, values)

            spec = yaml.dump(self.data, indent=2)
            spec = self.spec_replace(spec)

            variables = yaml.safe_load(spec)

            name = os.path.basename(self.script_out)
            script = f"{directory}/{identifier}/{name}"
            config = f"{directory}/{identifier}/config.yaml"

            variables.update({'experiment': permutation})
            variables["sbatch"]["identifier"] = identifier

            configuration[identifier] = {
                "id": identifier,
                "directory": f"{directory}/{identifier}",
                "experiment": assignments,
                "script": script,
                "config": config,
                "variables": variables
            }
        return configuration

    def generate_experiment_batch_scripts(self, out_mode=None):
        """
        Utility method to genrerate either hierarchical or flat outputs; or debug.

        NOte the falt mode is no longer supported

        :param out_mode: The mode of operation.  One of: "debug", "flat", "hierarchical"
        :type out_mode: string
        :return: generates the batch scripts
        :rtype: None
        """
        mode = self.execution_mode if out_mode is None else out_mode.lower()
        if mode.startswith("d"):
            Console.warning("This is just debug mode")
            print()
            for permutation in self.permutations:
                values = ""
                for attribute, value in permutation.items():
                    values = values + f"{attribute}={value} "
                script = f"{self.output_dir}/{self.script_out}{values}".replace("=", "_")
        else:
            if mode.startswith("f"):
                Console.error("Flat mode is no longer supported", traceflag=True)
                # configuration = self._generate_flat_config()
            elif mode.startswith("h"):
                configuration = self._generate_hierarchical_config()
            else:
                raise RuntimeError(f"Invalid generator mode {mode}")
            if self.verbose:
                banner("Script generation")

            print(Printer.write(configuration, order=["id", "experiment", "script", "config", "directory"]))

            self.configuration_parameters = configuration

            self.generate_setup_from_configuration(configuration)

    def generate_submit(self, name=None, job_type='slurm'):
        """
        Generates a list of commands based on the permutations for submission

        :param name: Name of the experiments
        :type name: str
        :param job_type: name of the job type used at submission such as
                         sbatch, slurm, jsrun, mpirun, sh, bash
        :type job_type: str
        :param verbose: prints the generated command lines
        :type verbose: bool
        :return: prepars the internal data for the experiments, if set to verbose, prints them
        :rtype: None
        """

        if ".json" not in name:
            name = f"{name}.json"

        if job_type == 'slurm':
            cmd = 'sbatch'
        elif job_type == 'lsf':
            cmd = 'bsub'
        else:
            cmd = job_type

        # else:
        #    raise RuntimeError(f"Unsupported submission type {type_}")

        experiments = json.loads(readfile(name))

       #  print (experiments)

        if experiments is None:
            Console.error("please define the experiment parameters")
            return ""

        for entry in experiments:
            if self.verbose:
                print(f"# Generate {entry}")
            experiment = experiments[entry]
            parameters = experiment["experiment"]
            directory = experiment["directory"]
            script = os.path.basename(experiment["script"])
            print(f"{parameters} cd {directory} && {cmd} {script}")

    def generate_setup_from_configuration(self, configuration):
        for identifier in configuration:
            experiment = configuration[identifier]
            Shell.mkdir(experiment["directory"])
            if self.verbose:
                print()
                Console.info(f"Setup experiment {identifier}")
                print(f"- Making dir {experiment['directory']}")
                print(f"- write file {experiment['config']}")

            # Generate UUID for each perm
            experiment["variables"]['sbatch']['uuid'] = str(uuid.uuid4())

            writefile(experiment["config"], yaml.dump(experiment["variables"], indent=2))
            content_config = readfile(experiment["config"])
            try:
                check = yaml.safe_load(content_config)
            except Exception as e:
                print(e)
                Console.error("We had issues with our check for the config.yaml file")

            content_script, replaced = self.generate(self.template_content, variables=experiment["variables"])

            # if self.verbose:
            #    for attribute, value in replaced.items():
            #        print (f"- replaced {attribute}={value}")

            writefile(experiment["script"], content_script)

    @property
    def now(self):
        """
        The time of now in the format "%Y-m-%d"
        :return: "%Y-m-%d"
        :rtype: str
        """
        return datetime.now().strftime("%Y-m-%d")

    def save_experiment_configuration(self, name=None):
        """
        Saves the experiment configuration in a json file

        :param name: name of the configuration file
        :type name: str
        :return: writes into the file with given name the json content
        :rtype: None
        """
        if name is not None:
            content = json.dumps(self.configuration_parameters, indent=2)
            writefile(name, content)
