
sbatch two [--config=CONFIG...] [--out=DESTINATION] [--attributes=PARAMS] [--gpu=GPU] SOURCE [--dryrun] [--noos] [--dir=DIR]

sbatch 
    --config=a.py,b.json,c.yaml
    --dir=     # cd dir
    rivanna.in.slurm    -> desination rivanna.slurm
    --attributes=\"a=1,b=5\" 

    --experiment=epoch=[0-10:2],gpus[1,2,4]

    for expemint in range(0-10:2):
       for gpus in [1,2,4]:

    --experiment=gpus[1,2,4],epoch=[0-10:2]

    for gpus in [1,2,4]:
       for expemint in range(0-10:2):

```
[--source=SOURCE]
    the source of a template. If the filename has an .in. included it will be removed to create the destination, if the --destination  parameter is not specified

[--destination=DESTINATION]
    if source is specified and destination is specified the source will be transformed into destination replacing all variables

[--config=CONFIG...]
    a. if the config file is a yaml file (*.yaml or *.yml), all variables defined in config are substituted
        if the file looks like
parameter:
  b: 1
then the variable with then name parameter.b will be substituted
    b. if the config file is a python program all variables defined in the file must be stored in a the python files in a flatdict (cloudmesh.vcoomon.flatdict) are replaced
from cloudmesh.common.Flatdict import FlatDict

data = {
    "name": "Gregor",
    "address": {
        "city": "Bloomington",
        "state": "IN"

    }
}

data = FlatDict(data, sep=".")
  Then for example the variable
   data.name
can be substituted in the source
    For examples see the code in github examples at ....
    c. if a python configparser is used all variables in it can be replaced. Different section names are preceeded by the sectionname.
        Assume the data is stored in configA.py such as
        [DEFAULT]
        a = 100
        Then in the source the variable with the following name will be substituted: DEFAULT.a
   d. if the configuration file is a json file the variables are substituted with a . in its name hierarchy
Note that multiple configuration files can be specified in multiple different formats

Examples:

   configuration_in_python.py:
   
data = {
    "name": "Gregor",
    "address": {
        "city": "Bloomington",
        "state": "IN"

    }
}

data = FlatDict(data, sep=".")
   
configuration_in_json. json

TBD use same example

configuration_in_yaml.yaml

TBD use same example

Please note that variables will be overwritten and the last value from an input configuration file will be the one used.

Please note that with the python configuration and flatdict automatic generation of variables can be achieved easily


```

