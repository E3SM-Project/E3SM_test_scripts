# Set up python
source  /lcrc/soft/climate/e3sm-unified/load_latest_cime_env.sh

source /home/software/spack-0.10.1/opt/spack/linux-centos7-x86_64/gcc-4.8.5/lmod-7.4.9-ic63herzfgw5u3na5mdtvp3nwxy6oj2z/lmod/lmod/init/sh

export MODULEPATH=$MODULEPATH:/software/centos7/spack-latest/share/spack/lmod/linux-centos7-x86_64/Core
export TERM=xterm
export PROJECT=condo

module load cmake/3.14.2-gvwazz3

RUNSCRIPT_FLAGS="--scratch-root /lcrc/group/e3sm2/`whoami`/scratch/anvil --baseline-root /lcrc/group/e3sm2/baselines/anvil/intel"
