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
import os

import textwrap

from cloudmesh.sbatch.command.sbatch import SbatchCommand

from pprint import pprint


def remove_spaces(content):
    result = Shell.oneline(content)
    return " ".join(result.split("&&"))
    # # print(f"{content = }")
    # stripped = content.replace(r"\n", " ")
    # # print(f"{repr(stripped) = }")
    # return stripped

@pytest.mark.incremental
class TestConfig:

    def test_help(self):
        Benchmark.Start()
        command = "cms sbatch help"
        # print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        # VERBOSE(result)

        assert "sbatch" in result

    def test_oneline_noos_command(self, cfg_dir, testdir, capfd):
        HEADING()
        Benchmark.Start()

        config_files = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        slurm_script = f"{testdir}/example.in/slurm.in.sh"
        attributes = "a=1,b=4"
        command = (f"cms sbatch generate {slurm_script} --verbose --config={config_files} --attributes={attributes} --dryrun "
                   f"--noos --dir={cfg_dir} --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")

        result = Shell.run(command)
        Benchmark.Stop()

        captured = capfd.readouterr()
        assert "Error" not in captured.err
        #assert "Error" not in result

    def test_oneline_os_command(self, cfg_dir, testdir, capfd):
        # HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"cms sbatch generate {testdir}/example.in/slurm.in.sh --verbose --config={config} --attributes=a=1,b=4 --dryrun "
            f"--dir={cfg_dir} --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
        result = Shell.run(command)
        Benchmark.Stop()

        # os.system(f"tree {cfg_dir}")

        result = capfd.readouterr()
        pprint(result.out)
        pprint(result.err)
        assert "Error" not in result.err
        assert f'name=Gregor' in result.out
        assert 'address=Seasame Str.' in result.out
        assert 'a=1' in result.out
        assert 'debug=True' in result.out
        assert os.environ["USERNAME"] in result.out

    def test_hierarchy(self, cfg_dir, testdir, capfd):
        # HEADING()
        # Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"""cms sbatch generate {testdir}/example.in/slurm.in.sh 
                   --config={config}
                   --attributes=a=1,b=4 
                   --noos
                   --dir={cfg_dir}/out
                   --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                   --name=a
                   --mode=h
            """)
        print(command)
        result = Shell.execute(command, shell=True)
        # Benchmark.Stop()
        VERBOSE(result)
        # os.system(f"tree {cfg_dir}")

        result = capfd.readouterr()
        print(result.out)
        print(result.err)
        assert "Error" not in result.err
        # for root, dirs, files in os.walk(cfg_dir):
        #     for fyle in files:
        #         print(os.path.join(root, fyle))
        # os.system(f"dir {cfg_dir}")
        # with open(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh") as slrm:
        #     script_out = slrm.read()
        #     print(script_out)
        assert 'name=Gregor' in result.err
        assert 'address=Seasame Str.' in result.err
        assert 'a=1' in result.err
        assert 'debug=True' in result.err
        assert os.environ["USER"] in result.err

    def test_flat(self, cfg_dir, testdir, capfd):
        HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                   --verbose 
                   --config={config}
                   --attributes=name=gregor,a=1,b=4 
                   --dryrun 
                   --noos 
                   --dir={cfg_dir} 
                   --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                   --mode=f 
                   --name=a
            """)
        print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        # VERBOSE(result)
        # os.system("tree build")

        result = capfd.readouterr()
        assert "Error" not in result.err

    def test_with_os(self, cfg_dir, testdir, capfd):
        HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={config}
                       --attributes=a=1,b=4 
                       --dir={cfg_dir} 
                       --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                       --name=a
                       --mode=h
            """
        )
        # print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        # VERBOSE(result)
        # os.system("tree build")

        result = capfd.readouterr()
        assert "Error" not in result.err

    def test_experiment_yaml_dict(self, cfg_dir, testdir, capfd):
        HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/c.yaml,{cfg_dir}/exp_str.yaml"
        command = remove_spaces(
            f"""
            cms sbatch generate {testdir}/example.in/slurm.in.sh 
                       --config={config}
                       --noos 
                       --dir=build
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        # print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        # print(result)

        result = capfd.readouterr()
        assert "Error" not in result.err

    def test_experiment_yaml_str(self, cfg_dir, capfd):
        HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/c.yaml,{cfg_dir}/exp_str.yaml"
        command = remove_spaces(
            f"""
            cms sbatch generate {cfg_dir}/example.in/slurm.in.sh 
                       --config={config}
                       --noos 
                       --dir=build
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        # print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        # print(result)

        result = capfd.readouterr()
        assert "Error" not in result.err

    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")
