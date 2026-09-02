#
source /gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/gcc-9.3.0/lmod-8.3-5be73rg/lmod/lmod/init/sh

# unload any previously loaded python, use python from load_latest_cime_env.sh
module unload python
source /lcrc/soft/climate/e3sm-unified/load_latest_cime_env.sh

export PROJECT=e3sm

RUNSCRIPT_FLAGS="--scratch-root /lcrc/group/e3sm2/`whoami`/scratch/chrys"
