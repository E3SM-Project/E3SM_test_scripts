# 
source  /lcrc/soft/climate/e3sm-unified/load_latest_cime_env.sh

source /gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/gcc-9.3.0/lmod-8.3-5be73rg/lmod/lmod/init/sh

# kokkos needs CMake 3.16 or higher. Default version is 3.11.4
module load cmake/3.19.1-yisciec
