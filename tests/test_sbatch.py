###############################################################
# pytest -v --capture=no tests/test_sbatch.py
# pytest -v  tests/test_sbatch.py
# pytest -v --capture=no  tests/test_sbatch.py::Test_sbatch::<METHODNAME>
###############################################################
import pytest
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

    def test_experiment_yaml_python_dict(self):
        HEADING()
        banner(os.getcwd())
        Benchmark.Start()
        for f in ["c.yaml", "exp_str.yaml", "exp_dict.yaml", "a.py", "slurm.in.sh"]:
            Shell.copy_file(f"{example}/{f}", f"{build_dir}/{f}")

        attributes = "a=1,b=4,g.a=4"
        attributes = "a=1,b=4"

        command = format_command(
            f"""
            cms sbatch generate 
                       --source=slurm.in.sh 
                       --config=c.yaml,a.py,exp_dict.yaml
                       --attributes={attributes}
            #           --noos 
            #           --nocm 
            #           --os=HOME,USER
                       --source_dir={example}
                       --output_dir={build_dir}
                       --mode=h
                       --name=a
                       --os=USER,HOME
                       --verbose
            #           --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\"
            """
        )
        print(command)

        print(build_dir)
        result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        # content = readfile(f"{build_dir}/slurm.sh")
        # assert "p_gregor=GREGOR" in content
        # assert "a=101" in content


class h:

    def test_experiment_yaml_python_flat(self):
        HEADING()
        banner(os.getcwd())
        Benchmark.Start()
        for f in ["c.yaml", "exp_str.yaml", "a.py", "slurm.in.sh"]:
            Shell.copy_file(f"{example}/{f}", f"{build_dir}/{f}")

        command = format_command(
            f"""
            cms sbatch generate 
                       --source=slurm.in.sh
                       --config=c.yaml,a.py
                       --noos 
                       --source_dir={example}
                       --output_dir={build_dir}
                       --mode=h
                       --name=a
                       --os=USER,HOME
            #           --flat
                       --verbose
            """
        )

        print(command)
        print(build_dir)
        result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        content = readfile(f"{build_dir}/slurm.in.sh")
        # assert "p_gregor=GREGOR" in content
        # assert "a=101" in content


class f:

    def test_experiment_yaml_python_a(self):
        HEADING()
        banner(os.getcwd())
        Benchmark.Start()
        for f in ["c.yaml", "exp_str.yaml", "a.py", "slurm.in.sh"]:
            Shell.copy_file(f"{example}/{f}", f"{build_dir}/{f}")

        command = format_command(
            f"""
            cms sbatch generate 
                       --source=slurm.in.sh 
                       --config=c.yaml,exp_str.yaml,a.py
                       --noos 
                       --source_dir={example}
                       --output_dir={build_dir}
                       --mode=h
                       --name=a
            """
        )

        print(command)
        print(build_dir)
        result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        content = readfile(f"{build_dir}/slurm.in.sh")
        # assert "p_gregor=GREGOR" in content
        # assert "a=101" in content


class ggg:

    def test_experiment_yaml_python(self):
        HEADING()
        banner(os.getcwd())
        Benchmark.Start()
        for f in ["c.yaml", "exp_str.yaml", "a.py", "slurm.in.sh"]:
            Shell.copy_file(f"{example}/{f}", f"{build_dir}/{f}")

        command = format_command(
            f"""
            cms sbatch generate slurm.in.sh 
                       --config={example}/c.yaml,{example}/exp_str.yaml,{example}/a.py
                       --noos 
                       --dir={build_dir}
                       --mode=h
                       --name=a
                       --verbose
            """
        )

        print(command)
        print(build_dir)
        result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        content = readfile(f"{build_dir}/slurm.in.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content


class res:
    def test_experiment_yaml_ipynb(self):
        HEADING()

        Benchmark.Start()
        command = format_command(
            f"""
            cms sbatch generate {tests_dir}/example.in/slurm.in.sh 
                       --config={example}/c.yaml,{example}/exp_str.yaml,{example}/a.py,{example}/d.ipynb
                       --noos 
                       --dir={build_dir}
                       --mode=h
                       --name=a
            """
        )

        result = Shell.run(command)
        Benchmark.Stop()

        content = readfile(f"{build_dir}/epoch_1_x_1/slurm.sh")
        # assert "p_gregor=GREGOR" in content
        assert "a=101" in content
        assert 'd="this is the way"' in content

    def test_oneline_noos_command(self):
        HEADING()

        Benchmark.Start()

        config_files = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        slurm_script = f"{tests_dir}/example.in/slurm.in.sh"
        attributes = "a=1,b=4"
        command = (f"cms sbatch generate {slurm_script} --verbose --config={config_files} --attributes={attributes} "
                   f"--noos --dir={build_dir} --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")

        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{build_dir}/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_oneline_os_command(self):
        HEADING()

        Benchmark.Start()
        config = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        command = format_command(
            f"cms sbatch generate {tests_dir}/example.in/slurm.in.sh --verbose --config={config} --attributes=a=1,b=4 --dryrun "
            f"--dir={build_dir} --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        assert 'name=Gregor' in result
        assert 'address="Seasame Str."' in result
        assert 'a=1' in result
        assert 'debug=True' in result
        # Github does not have a "USERNAME" that is set.
        if "GITHUB_ACTIONS" in os.environ:
            assert 'user={USERNAME}' in result
        else:
            assert f'user={os.environ["USERNAME"]}' in result

        content = readfile(f"{build_dir}/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_hierarchy(self):
        HEADING()

        Benchmark.Start()
        config = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        command = format_command(
            f"cms sbatch generate {tests_dir}/example.in/slurm.in.sh"
            f" --config={config}"
            f" --dir={build_dir}"
            " --attributes=a=1,b=4"
            # " --noos"
            " --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\""
            " --name=a"
            " --mode=h")
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result

        content = readfile(f"{build_dir}/epoch_1_x_1_y_10/slurm.sh")

        assert "p_gregor=GREGOR" in content
        assert "a=101" in content
        assert 'address="Seasame Str."' in content
        # BUG: testing assumes `cms debug on` has been run prior to execution
        #      need to enable this temporarily.
        assert 'debug=True' in content
        # Github does not have a "USERNAME" that is set.
        if "GITHUB_ACTIONS" in os.environ:
            assert 'user={USERNAME}' in content
        else:
            assert f'user={os.environ["USERNAME"]}' in content

        if "HOME" in os.environ:
            assert f'home={os.environ["HOME"]}' in content
        else:
            assert 'home={HOME}' in content

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

    def test_flat(self):
        HEADING()

        Benchmark.Start()
        config = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        command = format_command(
            f"""
            cms sbatch generate {tests_dir}/example.in/slurm.in.sh 
                   --verbose 
                   --config={config}
                   --attributes=name=gregor,a=1,b=4 
                   --noos
                   --nocm 
                   --dir={build_dir}
                   --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                   --mode=f 
                   --name=a
            """)
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        assert "p_gregor=GREGOR" in result
        assert "a=101" in result

        experiment_files = next(os.walk(f"{build_dir}"))[2]

        assert "slurm_epoch_1_x_1_y_10.sh" in experiment_files
        assert "slurm_epoch_1_x_1_y_11.sh" in experiment_files
        assert "slurm_epoch_1_x_4_y_10.sh" in experiment_files
        assert "slurm_epoch_1_x_4_y_11.sh" in experiment_files
        assert "slurm_epoch_2_x_1_y_10.sh" in experiment_files
        assert "slurm_epoch_2_x_1_y_11.sh" in experiment_files
        assert "slurm_epoch_2_x_4_y_10.sh" in experiment_files
        assert "slurm_epoch_2_x_4_y_11.sh" in experiment_files
        assert "slurm_epoch_3_x_1_y_10.sh" in experiment_files
        assert "slurm_epoch_3_x_1_y_11.sh" in experiment_files
        assert "slurm_epoch_3_x_4_y_10.sh" in experiment_files
        assert "slurm_epoch_3_x_4_y_11.sh" in experiment_files
        assert "config_epoch_1_x_1_y_10.yaml" in experiment_files
        assert "config_epoch_1_x_1_y_11.yaml" in experiment_files
        assert "config_epoch_1_x_4_y_10.yaml" in experiment_files
        assert "config_epoch_1_x_4_y_11.yaml" in experiment_files
        assert "config_epoch_2_x_1_y_10.yaml" in experiment_files
        assert "config_epoch_2_x_1_y_11.yaml" in experiment_files
        assert "config_epoch_2_x_4_y_10.yaml" in experiment_files
        assert "config_epoch_2_x_4_y_11.yaml" in experiment_files
        assert "config_epoch_3_x_1_y_10.yaml" in experiment_files
        assert "config_epoch_3_x_1_y_11.yaml" in experiment_files
        assert "config_epoch_3_x_4_y_10.yaml" in experiment_files
        assert "config_epoch_3_x_4_y_11.yaml" in experiment_files

    def test_with_os(self):
        HEADING()

        Benchmark.Start()
        config = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        command = format_command(
            f"""
            cms sbatch generate {tests_dir}/example.in/slurm.in.sh 
                       --config={config}
                       --attributes=a=1,b=4 
                       --dir={build_dir}
                       --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                       --name=a
                       --mode=h
            """
        )

        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{build_dir}/epoch_1_x_1_y_10/slurm.sh")

        assert "a=101" in content

    def test_experiment_yaml_dict(self):
        HEADING()

        Benchmark.Start()
        config = f"{example}/c.yaml,{example}/exp_str.yaml,{example}/a.py"
        command = format_command(
            f"""
            cms sbatch generate {tests_dir}/example.in/slurm.in.sh 
                       --config={config}
                       --noos 
                       --dir={build_dir}
                       --mode=h
                       --name=a
            """
        )

        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{build_dir}/epoch_1_x_1/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_experiment_yaml_str(self):
        HEADING()

        Benchmark.Start()
        config = f"{example}/c.yaml,{example}/exp_str.yaml,{example}/a.py"
        command = format_command(
            f"""
            cms sbatch generate {tests_dir}/example.in/slurm.in.sh 
                       --config={config}
                       --noos 
                       --dir={build_dir}
                       --mode=h
                       --name=a
            """
        )

        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{build_dir}/epoch_1_x_1/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_setupl_cli(self):
        HEADING()

        Benchmark.Start()

        config_files = f"{example}/a.py,{example}/b.json,{example}/c.yaml"
        slurm_script = f"{tests_dir}/example.in/slurm.in.sh"
        attributes = "a=1,b=4"
        command = f"cms sbatch generate --setup={example}/setup.yaml --attributes=a=101 --verbose"

        print(command)
        print(build_dir)
        print(example)
        print(tests_dir)

        with ctx_chdir(build_dir):
            result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{build_dir}/epoch_1_x_1_y_10/slurm.sh")
        config = readfile(f"{build_dir}/epoch_1_x_1_y_10/config.yaml")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_benchmark(self):
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")

    # def clean(self):
    #    os.system{"rm -rf build"}
