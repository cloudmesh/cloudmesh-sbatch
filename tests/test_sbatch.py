###############################################################
# cd tests; pytest -v --capture=no test_sbatch.py
# cd tests; pytest -v  test_sbatch.py
# cd tests; pytest -v --capture=no  test_sbatch.py::Test_sbatch::<METHODNAME>
###############################################################
import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import readfile
import os
import textwrap
from pprint import pprint
from contextlib import contextmanager


def remove_spaces(content):
    result = Shell.oneline(content)
    return " ".join(result.split(" && "))


@contextmanager
def ctx_chdir(path):
    current_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(current_dir)


@pytest.mark.incremental
class TestConfig:

    def test_help(self):
        Benchmark.Start()
        command = "cms sbatch help"
        result = Shell.run(command)
        Benchmark.Stop()

        assert "sbatch" in result

    def test_experiment_yaml_python(self, cfg_dir, testdir):
        HEADING()
        Benchmark.Start()
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={cfg_dir}/c.yaml,{cfg_dir}/exp_str.yaml,{cfg_dir}/a.py
                       --noos 
                       --dir={cfg_dir}/out
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        result = Shell.run(command)
        Benchmark.Stop()

        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_experiment_yaml_ipynb(self, cfg_dir, testdir):
        HEADING()
        Benchmark.Start()
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={cfg_dir}/c.yaml,{cfg_dir}/exp_str.yaml,{cfg_dir}/a.py,{cfg_dir}/d.ipynb
                       --noos 
                       --dir={cfg_dir}/out
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        result = Shell.run(command)
        Benchmark.Stop()

        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        # assert "p_gregor=GREGOR" in content
        assert "a=101" in content
        assert 'd="this is the way"' in content

    def test_oneline_noos_command(self, cfg_dir, testdir):
        Benchmark.Start()

        config_files = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        slurm_script = f"{testdir}/example.in/slurm.in.sh"
        attributes = "a=1,b=4"
        command = (f"cms sbatch generate {slurm_script} --verbose --config={config_files} --attributes={attributes} "
                   f"--noos --dir={cfg_dir}/out --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")

        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_oneline_os_command(self, cfg_dir, testdir):
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"cms sbatch generate {testdir}/example.in/slurm.in.sh --verbose --config={config} --attributes=a=1,b=4 --dryrun "
            f"--dir={cfg_dir}/out --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
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

        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_hierarchy(self, cfg_dir, testdir):
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"cms sbatch generate {testdir}/example.in/slurm.in.sh"
            f" --config={config}"
            f" --dir={cfg_dir}/out"
            " --attributes=a=1,b=4"
            # " --noos"
            " --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\""
            " --name=a"
            " --mode=h")
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result

        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")

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

        experiment_dirs = next(os.walk(f"{cfg_dir}/out"))[1]

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

    def test_flat(self, cfg_dir, testdir):
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                   --verbose 
                   --config={config}
                   --attributes=name=gregor,a=1,b=4 
                   --noos 
                   --dir={cfg_dir}/out
                   --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                   --mode=f 
                   --name=a
            """)
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        assert "p_gregor=GREGOR" in result
        assert "a=101" in result

        experiment_files = next(os.walk(f"{cfg_dir}/out"))[2]

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


    def test_with_os(self, cfg_dir, testdir):
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={config}
                       --attributes=a=1,b=4 
                       --dir={cfg_dir}/out
                       --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                       --name=a
                       --mode=h
            """
        )

        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")

        assert "a=101" in content

    def test_experiment_yaml_dict(self, cfg_dir, testdir):
        Benchmark.Start()
        config = f"{cfg_dir}/c.yaml,{cfg_dir}/exp_str.yaml,{cfg_dir}/a.py"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={config}
                       --noos 
                       --dir={cfg_dir}/out
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_experiment_yaml_str(self, cfg_dir, testdir):
        Benchmark.Start()
        config = f"{cfg_dir}/c.yaml,{cfg_dir}/exp_str.yaml,{cfg_dir}/a.py"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={config}
                       --noos 
                       --dir={cfg_dir}/out
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        result = Shell.run(command)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_yaml_cli(self, cfg_dir, testdir):
        Benchmark.Start()

        config_files = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        slurm_script = f"{testdir}/example.in/slurm.in.sh"
        attributes = "a=1,b=4"
        command = f"cms sbatch generate --setup={cfg_dir}/setup.yaml --attributes=a=101 --verbose"

        with ctx_chdir(cfg_dir):
            result = Shell.run(command)
        print(result)
        Benchmark.Stop()

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_benchmark(self):
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")
