#!/bin/bash

#SBATCH --job-name=gregors_test          # Job name
#SBATCH --mail-type=END,FAIL             # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=laszewski@gmail.com  # Where to send mail
#SBATCH --ntasks=1                       # Run on a single CPU
#SBATCH --mem=1gb                        # Job memory request
#SBATCH --time=00:05:00                  # Time limit hrs:min:sec
#SBATCH --output=x_gregors_test_%j.log    # Standard output and error log

echo "Node     :" $SLURMD_NODENAME
echo "Node List:" $SLURMD_NODENAME
echo "PWD      :" `pwd`
echo "Date     :" `date`

echo "Gregors Test"
date
time sleep 1
date
