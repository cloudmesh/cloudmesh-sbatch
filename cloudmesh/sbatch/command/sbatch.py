import pathlib

from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import banner
from cloudmesh.sbatch.sbatch import SBatch
from cloudmesh.sbatch.slurm import Slurm
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters


class SbatchCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_sbatch(self, args, arguments):
        r"""
        ::

          Usage:
                sbatch generate submit --name=NAME [--job_type=JOB_TYPE] [--verbose]
                sbatch generate --source=SOURCE --name=NAME
                                [--out=OUT]
                                [--verbose]
                                [--mode=MODE]
                                [--config=CONFIG]
                                [--attributes=PARAMS]
                                [--output_dir=OUTPUT_DIR]
                                [--dryrun]
                                [--noos]
                                [--os=OS]
                                [--nocm]
                                [--source_dir=SOURCE_DIR]
                                [--experiment=EXPERIMENT]
                                [--flat]
                sbatch slurm start
                sbatch slurm stop
                sbatch slurm info

          sbatch allows the creation of parameterized batch
          scripts. The initial support includes slurm, but we intend
          also to support LSF. Parameters can be specified on the
          commandline or in configuration files. Configuration files
          can be formulated as json,yaml, python, or jupyter
          notebooks.

          Parameters defined in this file are then used in the slurm
          batch script and substituted with their values. A special
          parameter called experiment defines a number of variables
          that are permuted on when used allowing multiple batch
          scripts to be defined easily to conduct parameter studies.

          Please note that the setup flag is deprecated and is in
          future versions fully covered while just using the config
          file.

          Arguments:
              FILENAME       name of a slurm script generated with sbatch
              CONFIG_FILE    yaml file with configuration
              ACCOUNT        account name for host system
              SOURCE         name for input script slurm.in.sh, lsf.in.sh,
                             script.in.sh or similar
              PARAMS         parameter lists for experimentation
              GPU            name of gpu

          Options:
              -h                        help
              --config=CONFIG...        a list of comma seperated configuration
                                        files in yaml or json format.
                                        The endings must be .json or .yaml
              --type=JOB_TYPE           The method to generate submission scripts.
                                        One of slurm, lsf. [default: slurm]
              --attributes=PARAMS       a list of coma separated attribute value pairs
                                        to set parameters that are used. [default: None]
              --output_dir=OUTPUT_DIR   The directory where the result is written to
              --source_dir=SOURCE_DIR   location of the input directory [default: .]
              --account=ACCOUNT         TBD
              --gpu=GPU                 The name of the GPU. Tyoically k80, v100, a100, rtx3090, rtx3080
              --noos                    ignores environment variable substitution from the shell. This
                                        can be helpfull when debugging as the list is quite lareg
              --nocm                    cloudmesh as a variable dictionary build in. Any vaiable referred to
                                        by cloudmesh. and its name is replaced from the
                                        cloudmesh variables
              --experiment=EXPERIMENT   This specifies all parameters that are used to create
                                        permutations of them.
                                        They are comma separated key value pairs
              --mode=MODE               one of "flat", "debug", "hierachical" can also just
                                        use "f". "d", "h" [default: h]
              --name=NAME               name of the experiment configuration file
              --os=OS                   Selected OS variables
              --flat                    produce flatdict
              --dryrun                  flag to do a dryrun and not create files and
                                        directories [default: False]
              --verbose                 Print more information when executing [default: False]

          Description:

            > Examples:
            >
            > cms sbatch generate slurm.in.sh --verbose \\
            >     --config=a.py,b.json,c.yaml \\
            >     --attributes=a=1,b=4 \\
            >     --dryrun --noos --input_dir=example \\
            >     --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \\
            >     --name=a --mode=h
            >
            > cms sbatch generate slurm.in.sh \\
            >    --config=a.py,b.json,c.yaml \\
            >    --attributes=a=1,b=4 \\
            >    --noos \\
            >    --input_dir=example \\
            >    --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \\
            >    --name=a \\
            >    --mode=h
            >
            > cms sbatch generate slurm.in.sh \\
            >    --verbose \\
            >    --config=a.py,b.json,c.yaml \\
            >    --attributes=name=gregor,a=1,b=4 \\
            >    --noos \\
            >    --input_dir=example \\
            >    --experiment="epoch=[1-3] x=[1,4] y=[10,11]" \\
            >    --mode=f \\
            >    --name=a
            >
            > cms sbatch generate slurm.in.sh --experiments-file=experiments.yaml --name=a
            >
            > cms sbatch generate submit --name=a

        """

        map_parameters(arguments,
                       "verbose",
                       "source",
                       "name",
                       "out",
                       "mode",
                       "config",
                       "attributes",
                       "output_dir",
                       "source_dir",
                       "experiment",
                       "account",
                       "filename",
                       "gpu",
                       "os",
                       "job_type",
                       "flat",
                       "dryrun")

        verbose = arguments["--verbose"]
        if verbose:
            banner("experiment batch generator")

        if arguments.slurm:
            if arguments.start:
                Slurm.start()
            elif arguments.stop:
                Slurm.stop()
            elif arguments.info:
                Slurm.status()

            return ""

        if arguments.name is not None:
            if not arguments.name.endswith(".json"):
                arguments.name = arguments.name + ".json"

        if verbose:
            VERBOSE(arguments)

        if arguments.generate and arguments.submit:

            #  sbatch generate submit --name=NAME [--job_type=JOB_TYPE] [--verbose]

            sbatch = SBatch()
            sbatch.verbose = arguments.verbose
            job_type = arguments.job_type or "slurm"
            sbatch.generate_submit(name=arguments.name, job_type=job_type)

            return ""

        elif arguments.generate:

            sbatch = SBatch()

            # CLI arguments override the experiments

            sbatch.dryrun = arguments.dryrun or False
            sbatch.verbose = arguments.verbose or False
            sbatch.execution_mode = arguments.mode or "h"
            sbatch.name = arguments.name
            sbatch.source = arguments.source
            sbatch.input_dir = str(Shell.map_filename(arguments["source_dir"]).path)
            sbatch.output_dir = str(Shell.map_filename(arguments["output_dir"]).path)
            sbatch.script_in = f"{sbatch.input_dir}/{sbatch.source}"

            #
            # set source and name
            #

            sbatch.name = arguments.name
            sbatch.source = arguments.source
            sbatch.source = SBatch.update_with_directory(sbatch.input_dir, sbatch.source)

            #
            # set output_script
            #
            if arguments.out is None:
                sbatch.script_out = pathlib.Path(sbatch.source).name.replace(".in.", ".")  # .replace(".in", "")
            else:
                sbatch.script_out = pathlib.Path(arguments.get('out', sbatch.script_out)).name
            sbatch.script_out = SBatch.update_with_directory(sbatch.output_dir, sbatch.script_out)

            #
            # make sure output script is not input script
            #
            if sbatch.source == sbatch.script_out:
                Console.error("The source and destination filenames are the same.", traceflag=True)
                return ""

            #
            # LOAD TEMPLATE
            #
            sbatch.load_source_template(sbatch.source)

            # order of replace is defined by
            # config
            # os
            # cm
            # attributes

            if arguments.config:

                # ok create list of config files
                try:
                    sbatch.config_files = arguments.config.split(",")
                    sbatch.config_files = [SBatch.update_with_directory(sbatch.input_dir, filename) for filename in
                                           sbatch.config_files]
                except Exception as e:
                    print(e)

                #
                # GENERATE THE REPLACEMENTS
                #

                for config_file in sbatch.config_files:
                    sbatch.update_from_file(config_file)

            if arguments.os:
                sbatch.os_variables = (arguments.os).split(",")
                sbatch.update_from_os(sbatch.os_variables)

            if not arguments["--noos"]:
                sbatch.update_from_os_environ()

            # replace variables from cm
            if not arguments["--nocm"]:
                sbatch.update_from_cm_variables()

            # expriments from commandline overwrites experiments in configs

            # if "experiment" in sbatch.data:
            #     try:
            #         d = sbatch.data["experiment"]
            #         print ("EEEEE", d, sbatch.permutation_generator(d))
            #         sbatch.experiment = sbatch.permutation_generator(d)
            #     except:
            #         pass

            if arguments.experiment:
                sbatch.experiments = arguments.experiment
                sbatch.experiment = sbatch.generate_experiment_permutations(sbatch.experiments)

            #
            #
            # result = sbatch.get_data(flat=arguments.flat)
            #
            # experiments = result["experiment"]
            # for e in experiments:
            #     experiments[e] = Parameter.expand(experiments[e])
            #
            # sbatch.permutations = sbatch.permutation_generator(experiments)

            # MOVE TO END
            #
            # ADD ADDITIONAL ATTRIBUTES
            #
            # move to last
            # if arguments.attributes:
            #    sbatch.attributes = arguments.attributes
            #    sbatch.update_from_attributes(arguments.attributes)

            sbatch.info()

            sbatch.generate_experiment_batch_scripts()

            sbatch.save_experiment_configuration(name=arguments.name)

            return ""

            # sbatch.config_from_cli(arguments)

            # sbatch.mode = arguments.mode
            # content = readfile(sbatch.source)

            # if sbatch.dryrun or verbose:
            #     banner("Configuration")
            #     print(sbatch.debug_state(key=".."))
            #     print()
            #     banner(f"Original Script {sbatch.source}")
            #     print(sbatch.template_content)
            #     banner("end script")
            # result = sbatch.generate(sbatch.template_content)
            #
            # if sbatch.dryrun or verbose:
            #     banner("Expanded Script")
            #     print(result)
            #     banner("Script End")
            # else:
            #     writefile(sbatch.script_out, result)
            #
            # sbatch.generate_experiment_batch_scripts()
            #
            # sbatch.save_experiment_configuration(name=arguments.name)

        return ""
