###############################################################
# pytest -v --capture=no tests/test_sbatch.py
# pytest -v  tests/test_sbatch.py
# pytest -v --capture=no  tests/test_sbatch..py::Test_sbatch::<METHODNAME>
###############################################################
import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
import os

def clean():
    os.system("	rm -rf test_test_example")

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
        result = Shell.execute(command, shell=True)
        Benchmark.Stop()
        VERBOSE(result)
        assert "sbatch" in result

    def test_oneline_command(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            "cms sbatch generate slurm.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun "
            "--noos --dir=test_example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" --name=a")
        print(command)
        # result = Shell.execute(command, shell=True)
        result = {"test": "sample"}
        Benchmark.Stop()
        VERBOSE(result)

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
                   --noos 
                   --dir=test_example 
                   --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" 
                   --name=a
            """)
        print(command)
        # result = Shell.execute(command, shell=True)
        result = {"test": "sample"}
        Benchmark.Stop()
        VERBOSE(result)

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
                   --dir=test_example 
                   --experiment="epoch=[1-3] x=[1,4] y=[10,11]" 
                   --mode=f 
                   --name=a
            """)
        print (command)
        #result = Shell.execute(command, shell=True)
        result = {"test": "sample"}
        Benchmark.Stop()
        VERBOSE(result)


    def test_with_os(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh 
                       --config=a.py,b.json,c.yaml 
                       --attributes=a=1,b=4 
                       --dir=test_example 
                       --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" 
                       --name=a
            """
        )
        print(command)
        # result = Shell.execute(command, shell=True)
        result = {"test": "sample"}
        Benchmark.Stop()
        VERBOSE(result)


    def test_experiment_yaml(self):
        HEADING()
        clean()
        Benchmark.Start()
        command = remove_spaces(
            """
            cms sbatch generate slurm.in.sh 
                       --config=c.yaml 
                       --experiment-file=experiments.yaml 
                       --noos 
                       --dir=test_example
            """
        )
        command = remove_spaces(command)
        print(command)
        # result = Shell.execute(command, shell=True)
        result = {"test": "sample"}
        Benchmark.Stop()
        VERBOSE(result)


    def test_benchmark(self):
        HEADING()
        Benchmark.print(csv=True, sysinfo=False, tag="cmd5")
