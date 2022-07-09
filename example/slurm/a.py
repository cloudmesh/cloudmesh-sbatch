from cloudmesh.common.FlatDict import FlatDict

data = {
    "name": "Gregor",
    "address": {
        "city": "Bloomington",
        "state": "IN"

    }
}

data = FlatDict(data, sep="__")
