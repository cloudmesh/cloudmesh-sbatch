###############################################################
# pytest -v --capture=no tests/test_sbatch.py
# pytest -v  tests/test_sbatch.py
# pytest -v --capture=no  tests/test_sbatch.py::Test_sbatch::<METHODNAME>
###############################################################
import pytest
import yaml

from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import FUNCTIONNAME
from cloudmesh.common.util import readfile
from cloudmesh.common.util import banner
import os
import re
import textwrap
from pprint import pprint
from contextlib import contextmanager
from pathlib import Path

BUILD_DIR = "tests/dest"

Shell.rmdir(BUILD_DIR)
Shell.mkdir(BUILD_DIR)
os.chdir(BUILD_DIR)

example = "../example.in"
tests_dir = ".."
build_dir = "."


def remove_spaces(content):

    result = Shell.oneline(content)
    result = " ".join(result.split(" && "))
    result = re.sub("\\s\\s+", " ", result)

    return result

def remove_comments(content):
    content = textwrap.dedent(content)
    lines = content.split("\n")
    lines = [line for line in lines if not line.startswith("#")]
    lines = "\n".join(lines)

    return lines

def format_command(content):

    result = remove_comments(content)
    print ("#", result)

    return remove_spaces(result)


@pytest.mark.incremental
class TestConfig:

    def test_help(self):
        Benchmark.Start()
        command = "cms sbatch help"
        result = Shell.run(command)
        Benchmark.Stop()
        # print (result)
        # assert "sbatch allows the creation of parameterized" in result
        assert "sbatch" in result

    def test_experiment_yaml_py(self):
        HEADING()
        banner(os.getcwd())
        Benchmark.Start()

        attributes = "a=1,b=4,g.a=4"
        attributes = "a=1,b=4"

        command = format_command(
            f"""
            cms sbatch generate 
                       --source=slurm.in.sh 
                       --config=c.yaml,a.py,exp_dict.yaml,d.ipynb
            #            --config=c.yaml
                       --attributes={attributes}
            #           --noos 
            #           --nocm 
                       --os=HOME,USER
                       --source_dir={example}
                       --output_dir={build_dir}
                       --mode=h
                       --name=a
            #           --verbose
            #           --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\"
            """
        )
        print(command)

        print(build_dir)
        result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        user = Shell.user()
        content = readfile(f"{build_dir}/epoch_1_x_1/slurm.sh")
        config = readfile(f"{build_dir}/epoch_1_x_1/config.yaml")
        print (content)
        assert "p_gregor=Gregor" in content
        assert "a=101" in content
        assert 'd="this is the way"' in content
        assert 'identifier="epoch_1_x_1"' in content
        assert f'USER: {user}' in config
        assert f'SHELL: ' in config

    def test_experiment_yaml_py(self):
        HEADING()
        banner(os.getcwd())
        Benchmark.Start()

        attributes = "a=1,b=4,g.a=4"
        attributes = "a=1,b=4"

        command = format_command(
            f"""
            cms sbatch generate 
                       --source=slurm.in.sh 
                       --config=c.yaml,a.py,exp_dict.yaml,d.ipynb
            #            --config=c.yaml
                       --attributes={attributes}
                       --noos 
            #           --nocm 
                       --os=HOME,USER
                       --source_dir={example}
                       --output_dir={build_dir}
                       --mode=h
                       --name=a
            #           --verbose
            #           --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\"
            """
        )
        print(command)

        print(build_dir)
        result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        user = Shell.user()
        content = readfile(f"{build_dir}/epoch_1_x_1/slurm.sh")
        config = readfile(f"{build_dir}/epoch_1_x_1/config.yaml")
        assert "p_gregor=Gregor" in content
        assert "a=101" in content
        assert 'd="this is the way"' in content
        assert 'identifier="epoch_1_x_1"' in content
        assert f'SHELL: ' not in config


    def test_hierarchy(self):
        HEADING()

        Shell.run("cms debug on")
        attributes = "a=1,b=4"
        Benchmark.Start()
        config = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        command = format_command(
            f"""
            cms sbatch generate 
                      --source=slurm.in.sh 
                      --config=c.yaml,a.py,exp_dict.yaml,d.ipynb
            #            --config=c.yaml
                      --attributes={attributes}
                      --noos 
            #           --nocm 
                      --os=HOME,USER
                      --source_dir={example}
                      --output_dir={build_dir}
                      --mode=h
                      --name=a
            #           --verbose
                       --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\"
            """)
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result

        content = readfile(f"{build_dir}/epoch_1_x_1_y_10/slurm.sh")

        assert "p_gregor=Gregor" in content
        assert "a=101" in content
        assert 'address="Seasame Str."' in content
        assert 'debug=True' in content

        experiment_dirs = next(os.walk(f"{build_dir}"))[1]

        assert "epoch_1_x_1_y_10" in experiment_dirs
        assert "epoch_1_x_1_y_11" in experiment_dirs
        assert "epoch_1_x_4_y_10" in experiment_dirs
        assert "epoch_1_x_4_y_11" in experiment_dirs
        assert "epoch_2_x_1_y_10" in experiment_dirs
        assert "epoch_2_x_1_y_11" in experiment_dirs
        assert "epoch_2_x_4_y_10" in experiment_dirs
        assert "epoch_2_x_4_y_11" in experiment_dirs
        assert "epoch_3_x_1_y_10" in experiment_dirs
        assert "epoch_3_x_1_y_11" in experiment_dirs
        assert "epoch_3_x_4_y_10" in experiment_dirs
        assert "epoch_3_x_4_y_11" in experiment_dirs

    # flat mode is no longer supported
    # def test_flat(self):
    #     HEADING()
    #
    #     Benchmark.Start()
    #     config = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
    #     command = format_command(
    #         f"""
    #         cms sbatch generate {tests_dir}/example.in/slurm.in.sh
    #                --verbose
    #                --config={config}
    #                --attributes=name=gregor,a=1,b=4
    #                --noos
    #                --nocm
    #                --dir={build_dir}
    #                --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\"
    #                --mode=f
    #                --name=a
    #         """)
    #     result = Shell.run(command)
    #     Benchmark.Stop()
    #
    #     content = readfile(f"{build_dir}/epoch_1_x_1/slurm.sh")
    #     config = readfile(f"{build_dir}/epoch_1_x_1/config.yaml")
    #
    #     assert "p_gregor=Gregor" in content
    #     assert "a=101" in content
    #     assert 'd="this is the way"' in content
    #     assert 'identifier="epoch_1_x_1"' in content
    #     assert f'SHELL: ' not in config
    #
    #     experiment_files = next(os.walk(f"{build_dir}"))[2]
    #
    #     assert "slurm_epoch_1_x_1_y_10.sh" in experiment_files
    #     assert "slurm_epoch_1_x_1_y_11.sh" in experiment_files
    #     assert "slurm_epoch_1_x_4_y_10.sh" in experiment_files
    #     assert "slurm_epoch_1_x_4_y_11.sh" in experiment_files
    #     assert "slurm_epoch_2_x_1_y_10.sh" in experiment_files
    #     assert "slurm_epoch_2_x_1_y_11.sh" in experiment_files
    #     assert "slurm_epoch_2_x_4_y_10.sh" in experiment_files
    #     assert "slurm_epoch_2_x_4_y_11.sh" in experiment_files
    #     assert "slurm_epoch_3_x_1_y_10.sh" in experiment_files
    #     assert "slurm_epoch_3_x_1_y_11.sh" in experiment_files
    #     assert "slurm_epoch_3_x_4_y_10.sh" in experiment_files
    #     assert "slurm_epoch_3_x_4_y_11.sh" in experiment_files
    #     assert "config_epoch_1_x_1_y_10.yaml" in experiment_files
    #     assert "config_epoch_1_x_1_y_11.yaml" in experiment_files
    #     assert "config_epoch_1_x_4_y_10.yaml" in experiment_files
    #     assert "config_epoch_1_x_4_y_11.yaml" in experiment_files
    #     assert "config_epoch_2_x_1_y_10.yaml" in experiment_files
    #     assert "config_epoch_2_x_1_y_11.yaml" in experiment_files
    #     assert "config_epoch_2_x_4_y_10.yaml" in experiment_files
    #     assert "config_epoch_2_x_4_y_11.yaml" in experiment_files
    #     assert "config_epoch_3_x_1_y_10.yaml" in experiment_files
    #     assert "config_epoch_3_x_1_y_11.yaml" in experiment_files
    #     assert "config_epoch_3_x_4_y_10.yaml" in experiment_files
    #     assert "config_epoch_3_x_4_y_11.yaml" in experiment_files


    def test_benchmark(self):
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")

    # def clean(self):
    #    os.system{"rm -rf build"}
