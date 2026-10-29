#
source /gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/gcc-9.3.0/lmod-8.3-5be73rg/lmod/lmod/init/sh

# Need older python to ensure CIME will work, especially with maint
# branches that use old CIME.
module load python/3.10.12
