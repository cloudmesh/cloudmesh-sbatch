###############################################################
# cd tests; pytest -v --capture=no test_config_sbatch.py
# cd tests; pytest -v  test_config_sbatch.py
# cd tests; pytest -v --capture=no  test_config_sbatch.py::test_config_sbatch::<METHODNAME>
###############################################################
import pytest
from cloudmesh.common.Benchmark import Benchmark
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.util import FUNCTIONNAME
from cloudmesh.common.util import readfile
import os
import shutil
import textwrap
from pprint import pprint
from contextlib import contextmanager
from pathlib import Path

BUILD_DIR = "tests/build"

def remove_spaces(content):
    result = Shell.oneline(content)
    return " ".join(result.split(" && "))

Shell.mkdir(BUILD_DIR)
os.chdir(BUILD_DIR)

cfg = "../../example/slurm"

@pytest.mark.incremental
class TestConfigSbatch:

    #def test_config_experiments(self):
    # uses example.in/experiments.yaml

    def test_config_experiment(self):
        HEADING()

        config_yaml = "experiments.yaml"

        name = FUNCTIONNAME()

        config = f"{cfg}/a.py,{cfg}/b.json,{cfg}/experiments.yaml"
        out_dir= "out"
        command = remove_spaces(
            f"cms sbatch generate {cfg}/slurm.in.sh"
            f" --config={config}"
            f" --dir={out_dir}"
            " --attributes=a=1,b=4"
            # " --noos"
            # " --experiment=\\\"epoch=[1-3] x=[1,4] y=[10,11]\\\""
            " --name=a"
            " --mode=h")
        result = Shell.run(command)
        print(result)

        assert "Error" not in result

        content = readfile(f"{out_dir}/epoch_1_x_1_y_10/slurm.sh")

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

        experiment_dirs = next(os.walk(f"{out_dir}"))[1]

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


    # def test_benchmark(self):
    #     Benchmark.print(csv=True, sysinfo=False, tag="cmd5")

    # def test_clean(self):
    #    os.system{"rm -rf build"}
