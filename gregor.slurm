#!/bin/bash

#SBATCH --job-name=gregors_test          # Job name
#RRR SBATCH --mail-type=END,FAIL             # Mail events (NONE, BEGIN, END, FAIL, ALL)
#RRR  SBATCH --mail-user=laszewski@gmail.com  # Where to send mail	
#RRR SBATCH --ntasks=1                       # Run on a single CPU
#RRR SBATCH --mem=1gb                        # Job memory request
#RRR SBATCH --time=00:05:00                  # Time limit hrs:min:sec
#RRR SBATCH --output=sgregors_test_%j.log    # Standard output and error log

pwd; hostname; date

echo "Gregors Test"
date
#sleep(30)
date
