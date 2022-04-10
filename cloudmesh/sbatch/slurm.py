"""Management of Slurm on the localhost.

This command is useful if you like to develop
advances APIs using slurm, but do not want to do
it on a production computer.

Curerntly onlu ubuntu 20.04 is supported.

The service can either be used as a commandline tool or as API.
If you  use the commandline YOU wnat to do the following.
First, you need to start the service with::

    cms sbatch slurm start

Next, you can test the status with::

    cms sbatch slurm status

To submit jobs you can now use the regular slurm commands such as::

    srun
    sbatch
    squeue

To stop the service please use::

    cms sbatch slurm stop

The API reflects what we do on the commandline and we have the methods::

    Slurm.start()
    Slurm.stop()
    Slurm.status()
"""
import os
from cloudmesh.common.util import banner

class Slurm:

    @staticmethod
    def start():
        """
        Starts the SLurm service oon your local machine.

        Returns:
            On stdout prints the action information
        """
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
        """
        Stops the SLurm service oon your local machine.

        Returns:
            On stdout prints the action information
        """
        os.system("sudo systemctl stop slurmd")
        os.system("sudo systemctl stop slurmctld")

    @staticmethod
    def status():
        """
        Shows the status of the SLurm service oon your local machine.

        Returns:
            On stdout prints the action information
        """

        for command in ["sudo tail /var/log/slurm-llnl/slurmd.log",
                        "sudo tail /var/log/slurm-llnl/slurmctld.log",
                        "sinfo -R"]:
            banner(command)
            os.system(command)