import pytest

from cloudmesh.common import path_expand
import pathlib
import shutil
import os
import sys
import tempfile

BUILD_DIR = "build"

def create_build(name=None):
    if name is None:
        os.system(f"mkdir -p build")
    else:
        os.system(f"mkdir -p build/{name}")


@pytest.fixture
def testdir():
    yield pathlib.Path(__file__).parent.as_posix()


@pytest.fixture
def builddir():
    yield pathlib.Path(__file__).parent.as_posix() + "/build"

@pytest.fixture
def cfg_dir(testdir, builddir):
    with tempfile.TemporaryDirectory(dir=builddir) as d:
        source = os.path.join(testdir, "example.in")
        target = os.path.join(d, 'build')
        shutil.copytree(source, target, dirs_exist_ok=True)

        yield pathlib.Path(target).as_posix()

        print("Directory out")
        for base, dirs, files in os.walk(d):
            for fyle in files:
                print(os.path.join(base, fyle), file=sys.stdout)


@pytest.fixture
def do_sbatch_args(cfg_dir):
    return (('generate slurm.in.sh --verbose'
             f' --config={cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml'
             ' --attributes=a=1,b=4'
             ' --dir=testing'
             ' --experiment="epoch=[1-3] x=[1,4] y=[10,11]"'
             ' --name=a'
             ' --mode=h'
             ' --noos'),
            { '--attributes': 'a=1,b=4',
              '--config'    : f"{cfg_dir}/a.py,{cfg_dir}/b.json,{cfg_dir}/c.yaml",
              '--dir'       : 'testing',
              '--dryrun'    : False,
              '--experiment': 'epoch=[1-3] x=[1,4] y=[10,11]',
              '--gpu'       : None,
              '--mode'      : 'h',
              '--name'      : 'a',
              '--nocm'      : False,
              '--noos'      : True,
              '--out'       : None,
              '--verbose'   : True,
              'SOURCE'      : f"{cfg_dir}/slurm.in.sh",
              'account'     : None,
              'attributes'  : 'a=1,b=4',
              'config'      : 'a.py,b.json,c.yaml',
              'dryrun'      : False,
              'experiment'  : 'epoch=[1-3] x=[1,4] y=[10,11]',
              'filename'    : None,
              'generate'    : True,
              'gpu'         : None,
              'info'        : False,
              'mode'        : 'h',
              'name'        : 'a',
              'out'         : None,
              'slurm'       : False,
              'start'       : False,
              'stop'        : False,
              'submit'      : False
              })
