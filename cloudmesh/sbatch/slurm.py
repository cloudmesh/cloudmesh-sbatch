import os
from cloudmesh.common.util import banner

class Slurm:

    @staticmethod
    def start():
        banner("Begin SLURM startup)")
        os.system("sudo systemctl start slurmctld")
        os.system("sudo systemctl start slurmd")
        os.system("sudo scontrol update nodename=white state=idle")
        banner("sinfo")
        os.system("sinfo")
        banner("squeue")
        os.system("squeue")
        banner("End of SLURM startup ")

    @staticmethod
    def stop():
        os.system("sudo systemctl stop slurmd")
        os.system("sudo systemctl stop slurmctld")

    @staticmethod
    def status():
        for command in ["sudo tail /var/log/slurm-llnl/slurmd.log",
                        "sudo tail /var/log/slurm-llnl/slurmctld.log",
                        "sinfo -R"]:
            banner(command)
            os.system(command)