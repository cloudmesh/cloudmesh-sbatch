test0:
	cms sbatch generate lsf.in.sh --verbose --config=a.py,b.json,c.yaml --attributes=a=1,b=4 --dryrun --noos --dir=example --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" --name=a

test1: clean
	cms sbatch generate lsf.in.sh --verbose \
                   --config=a.py,b.json,c.yaml \
                   --attributes=a=1,b=4 \
                   --dryrun \
                   --noos \
                   --dir=example \
                   --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \
                   --name=a 

test2: clean
	cms sbatch generate lsf.in.sh \
                   --config=a.py,b.json,c.yaml \
                   --attributes=a=1,b=4 \
                   --noos \
                   --dir=example \
                   --experiment=\"epoch=[1-3] x=[1,4] y=[10,11]\" \
                   --name=a

test3: clean
	cms sbatch generate lsf.in.sh \
                   --verbose \
                   --config=a.py,b.json,c.yaml \
                   --attributes=name=gregor,a=1,b=4 \
                   --dryrun \
                   --noos \
                   --dir=example \
                   --experiment="epoch=[1-3] x=[1,4] y=[10,11]" \
                   --mode=f \
                   --name=a 

test4: clean
	cms sbatch generate lsf.in.sh \
                   --config=c.yaml \
                   --experiment-file=experiments.yaml \
                   --noos \
                   --dir=example

# add other tests

cleaan:
	rm -rf example
