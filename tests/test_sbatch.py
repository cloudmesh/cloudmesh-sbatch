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


def remove_spaces(content):
    result = Shell.oneline(content)
    return " ".join(result.split(" && "))


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
        print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        pprint(result)

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
        print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        pprint(result)

        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        # assert "p_gregor=GREGOR" in content
        assert "a=101" in content
        assert 'd="this is the way"' in content

    def test_oneline_noos_command(self, cfg_dir, testdir):
        HEADING()
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
        # HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        command = remove_spaces(
            f"cms sbatch generate {testdir}/example.in/slurm.in.sh --verbose --config={config} --attributes=a=1,b=4 --dryrun "
            f"--dir={cfg_dir}/out --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
        result = Shell.run(command)
        Benchmark.Stop()

        # os.system(f"tree {cfg_dir}")

        # result = capfd.readouterr()
        pprint(result)
        assert "Error" not in result
        assert 'name=Gregor' in result
        assert 'address="Seasame Str."' in result
        assert 'a=1' in result
        assert 'debug=True' in result
        assert os.environ["USERNAME"] in result
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_hierarchy(self, cfg_dir, testdir):
        # HEADING()
        Benchmark.Start()
        config = f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml"
        # command = remove_spaces(
        #     f"cms sbatch generate {testdir}/example.in/slurm.in.sh --verbose --config={config} --attributes=a=1,b=4 --dryrun "
        #     f"--dir={cfg_dir}/out --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
        command = remove_spaces(
            f"cms sbatch generate {testdir}/example.in/slurm.in.sh"
            f" --config={config}"
            f" --dir={cfg_dir}/out"
            " --attributes=a=1,b=4"
            " --noos"
            " --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\""
            " --name=a"
            " --mode=h")
        result = Shell.run(command)
        Benchmark.Stop()
        pprint(result)

        assert "Error" not in result
        assert 'name=Gregor' in result
        assert 'address="Seasame Str."' in result
        assert 'a=1' in result
        assert 'debug=True' in result
        assert os.environ["USER"] in result

        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content
        assert 'address="Seasame Str."' in result
        assert 'debug=True' in result
        assert os.environ["USER"] in result

    def test_flat(self, cfg_dir, testdir):
        HEADING()
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
        print(command)
        result = Shell.run(command)
        Benchmark.Stop()

        pprint(result)
        # VERBOSE(result)
        # os.system("tree build")

        # result = capfd.readouterr()
        assert "Error" not in result
        # content = readfile(f"{cfg_dir}/out/slurm_epoch_1_x_1_y_10.sh")
        assert "p_gregor=GREGOR" in result
        assert "a=101" in result

    def test_with_os(self, cfg_dir, testdir):
        HEADING()
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
        # print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        # VERBOSE(result)
        # os.system("tree build")

        # result = capfd.readouterr()
        # assert "Error" not in result.err
        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1_y_10/slurm.sh")
        # assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_experiment_yaml_dict(self, cfg_dir, testdir):
        HEADING()
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
        # print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        # print(result)

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        # assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_experiment_yaml_str(self, cfg_dir, testdir):
        HEADING()
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
        # print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        # print(result)

        assert "Error" not in result
        content = readfile(f"{cfg_dir}/out/epoch_1_x_1/slurm.sh")
        assert "p_gregor=GREGOR" in content
        assert "a=101" in content

    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")
