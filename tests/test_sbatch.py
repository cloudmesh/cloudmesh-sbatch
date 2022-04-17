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

def clean():
    os.system("rm -rf build")
    os.system("cp -r example.in build")

def remove_spaces(content):
    result = Shell.oneline(content, seperator=" ")
    return " ".join(result.split())

@pytest.mark.incremental
class TestConfig:



    def test_help(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = "cms sbatch help"
        print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        VERBOSE(result)

        assert "sbatch" in result


    def test_oneline_noos_command(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            "cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun "
            "--noos --dir=build --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
        print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        VERBOSE(result)
        os.system("tree build")

        assert "Error" not in result


    def test_oneline_os_command(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            "cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun "
            "--dir=build --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" --name=a --mode=h")
        print(command)
        result = Shell.run(command)
        Benchmark.Stop()
        VERBOSE(result)
        os.system("tree build")

        assert "Error" not in result
        assert 'name=Gregor' in result
        assert 'address=Seasame Str.' in result
        assert 'a=1' in result
        assert 'debug=True' in result
        assert os.environ["USER"] in result


    def test_hierachy(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh --verbose 
                   --config=a.py,b.json,c.yaml 
                   --attributes=a=1,b=4 
                   --dryrun 
                   --dir=build 
                   --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                   --name=a
                   --mode=h
            """)
        print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        VERBOSE(result)
        os.system("tree build")

        assert "Error" not in result
        assert 'name=Gregor' in result
        assert 'address=Seasame Str.' in result
        assert 'a=1' in result
        assert 'debug=True' in result
        assert os.environ["USER"] in result

    def test_flat(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh 
                   --verbose 
                   --config=a.py,b.json,c.yaml 
                   --attributes=name=gregor,a=1,b=4 
                   --dryrun 
                   --noos 
                   --dir=build 
                   --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                   --mode=f 
                   --name=a
            """)
        print (command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        VERBOSE(result)
        os.system("tree build")

        assert "Error" not in result


    def test_with_os(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh 
                       --config=a.py,b.json,c.yaml 
                       --attributes=a=1,b=4 
                       --dir=build 
                       --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\" 
                       --name=a
                       --mode=h
            """
        )
        print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        VERBOSE(result)
        os.system("tree build")

        assert "Error" not in result

    def test_experiment_yaml_dict(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh 
                       --config=c.yaml,exp_str.yaml 
                       --noos 
                       --dir=build
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        print(result)

        assert "Error" not in result

    def test_experiment_yaml_str(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh 
                       --config=c.yaml,exp_str.yaml 
                       --noos 
                       --dir=build
                       --mode=h
                       --name=a
            """
        )
        command = remove_spaces(command)
        print(command)
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        print(result)

        assert "Error" not in result

    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")
