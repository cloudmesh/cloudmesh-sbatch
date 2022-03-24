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

class SBatch:

    def __init__(self, verbose=False):
        banner("init")
        self.data = {}
        self.template = None
        self.verbose = verbose
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


    def update_from_file(self, filename):
        if self.verbose:
            print(f"Reading variables from {filename}")

        suffix = pathlib.Path(filename).suffix
        content = readfile(filename)

        if suffix.lower() in [".json"]:
            values = dict(FlatDict(json.loads(content), sep="__"))
            self.data.update(values)
        elif suffix.lower() in [".yaml"]:
            content = readfile(filename)
            values = dict(FlatDict(yaml.safe_load(content), sep="__"))
            self.data.update(values)
        elif suffix.lower() in [".py"]:
            Console.red("# ERROR: Importing python not yet implemented")
        elif suffix.lower() in [".ipynb"]:
            Console.red("# ERROR: Importing jupyter notebooks not yet implemented")
        return self.data


    def generate(self, script):
        self.script = script
        self.content = script.format(**self.data)
        return self.content

    @property
    def now(self):
        # there is a better way ;)
        return Shell.run("date").strip().replace(" ", "-")

    def __str__(self):
        return self.content

    def configure_sbatch(self,host):
        """
        TODO: this is all hardcoded and must be changed

        Set the sbatch environmental variables based on yaml values
        Append the variables to the users environment
        """
        defaults = self.yaml['sbatch_setup'][f'{host}-{self.gpu}']
        user = self.env['USER']
        sbatch_vars = {
            'SBATCH_GRES': f'gpu:{defaults["card_name"]}:{defaults["num_gpus"]}',
            'SBATCH_JOB_NAME': f'mlcommons-science-earthquake-{user}',
            'SBATCH_CPUS_ON_NODE': str(defaults['num_cpus']),
            'SBATCH_TIMELIMIT': defaults['time'],
        }
        for var, value in sbatch_vars.items():
            self.env[str(var)] = value
        return self

    def get_parameters(self):
        #TODO finish when we decide how to impliment parameters
        # already have most of the logic established for passing in
        #  the parameters to the class
        return -1

    def update(self, *args):
        #TODO will update parameters
        # replace with the ergv and with the os.environ variables.
        #self.content = self.content.format(**argv, **os.environ, date=self.now)
        return -1

    def save(self, filename):
        """
        Writes the custom slurm script to a file for submission
        If the file already exists, the user will be prompted to override
        """
        if os.path.exists(path_expand(filename)):
            if yn_choice(f"{filename} exists, would you like to overwrite?"):
                writefile(filename, self.content)
        else:
            writefile(filename, self.content)

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


    def template(self):
        #
        # we could also replace other things such as BASE ...
        #
        script = textwarp.dedent(
            """
            #!/usr/bin/env bash

            #SBATCH --job-name=mlcommons-science-earthquake-{user}-{date}-a100
            #SBATCH --output=mlcommons-science-earthquake-{user}-{date}-a100.out
            #SBATCH --error=mlcommons-science-earthquake-{user}-{date}-a100.err
            #SBATCH --partition=gpu
            #SBATCH --cpus-per-task=6
            #SBATCH --mem=32G
            #SBATCH --time=06:00:00
            #SBATCH --gres=gpu:a100:1
            #SBATCH --account=ds6011-sp22-002
            
            
            ### TODO -figure out how to parameterize.
            #rSBATCH --job-name=mlcommons-science-earthquake-${GPU}-${PYTHON}
            #rSBATCH --output=mlcommons-science-earthquake-${GPU}-${PYTHON}.out
            #rSBATCH --error=mlcommons-science-earthquake-${GPU}-${PYTHON}.err
            #rSBATCH --partition=gpu
            #rSBATCH -c 1
            #rSBATCH --time=03:00:00
            #rSBATCH --gres=gpu:a100:1
            #rSBATCH --account=ds6011-sp22-002
            
            #  one proposal. lets do what robert does ...
            #
            #   git clone ....
            #   git clone ....
            #   ls ./mlcommons
            #   ls ./mlcommons-data-earthquake/data.tar.xz
            #   tar xvf mlcommons-data-earthquake/data.tar.xz
            #   ls ./data/EarthquakeDec2020
            #
            
            GPU_TYPE="a100"
            PYTHON_MAJ="3.10"
            PYTHON_MIN="2"
            
            RESOURCE_DIR="/project/ds6011-sp22-002"
            
            BASE=/scratch/$USER/${{GPU_TYPE}}
            HOME=${{BASE}}
            
            REV="mar2022"
            VARIANT="-gregor"
            
            echo "Working in <$(pwd)>"
            echo "Base directory in <${{BASE}}>"
            echo "Overridden home in <${{HOME}}>"
            echo "Revision: <${{REV}}>"
            echo "Variant: <${{VARIANT}}>"
            echo "Python: <${{PYTHON_MAJ}.${{PYTHON_MIN}}>"
            echo "GPU: <${{GPU_TYPE}}>"
            
            module load cuda cudnn
            
            nvidia-smi
            
            mkdir -p ${{BASE}}
            cd ${{BASE}}
            
            if [ ! -e "${{BASE}}/.local/python/${PYTHON_MAJ}.${PYTHON_MIN}" ] ; then
                tar Jxvf "${RESOURCE_DIR}/python-${PYTHON_MAJ}.${PYTHON_MIN}.tar.xz" -C "${{BASE}}"
            fi
            
            export LD_LIBRARY_PATH=${{BASE}}/.local/ssl/lib:$LD_LIBRARY_PATH
            echo "Python setup"
            
            if [ ! -e "${{BASE}}/ENV3/bin/activate" ]; then
                ${{BASE}}/.local/python/${PYTHON_MAJ}.${PYTHON_MIN}/bin/python3.10 -m venv ${{BASE}}/ENV3
            fi
            
            echo "ENV3 Setup"
            source ${{BASE}}/ENV3/bin/activate
            python -m pip install -U pip wheel papermill
            
            if [ ! -e "${{BASE}}/mlcommons-data-earthquake" ]; then
                git clone https://github.com/laszewsk/mlcommons-data-earthquake.git "${{BASE}}/mlcommons-data-earthquake"
            else
                (cd ${{BASE}}/mlcommons-data-earthquake ; \
                    git fetch origin ; \
                    git checkout main ; \
                    git reset --hard origin/main ; \
                    git clean -d --force)
            fi
            
            if [ ! -e "${{BASE}}/mlcommons" ]; then
                git clone https://github.com/laszewsk/mlcommons.git "${{BASE}}/mlcommons"
            else
                (cd ${{BASE}}/mlcommons ; \
                    git fetch origin ; \
                    git checkout main ; \
                    git reset --hard origin/main ; \
                    git clean -d --force)
            fi
            
            if [ ! -e ${{BASE}}/mlcommons/benchmarks/earthquake/data/EarthquakeDec2020 ]; then
                tar Jxvf ${{BASE}}/mlcommons-data-earthquake/data.tar.xz \
                    -C ${{BASE}}/mlcommons/benchmarks/earthquake
                mkdir -p ${{BASE}}/mlcommons/benchmarks/earthquake/data/EarthquakeDec2020/outputs
            fi
            
            
            (cd ${{BASE}}/mlcommons/benchmarks/earthquake/${REV} && \
                python -m pip install -r requirements.txt)
            
            
            (cd ${{BASE}}/mlcommons/benchmarks/earthquake/${REV} && \
                cp "FFFFWNPFEARTHQ_newTFTv29${VARIANT}.ipynb" FFFFWNPFEARTHQ_newTFTv29-$USER.ipynb)
            (cd mlcommons/benchmarks/earthquake/mar2022 && \
                papermill FFFFWNPFEARTHQ_newTFTv29-$USER.ipynb FFFFWNPFEARTHQ_newTFTv29-$USER-$GPU_TYPE.ipynb --no-progress-bar --log-output --log-level INFO)
            """
        )
