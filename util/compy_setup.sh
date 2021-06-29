source /share/apps/E3SM/conda_envs/load_latest_cime_env.sh
ulimit -c 0

# kokkos needs CMake 3.16 or higher.
module load cmake/3.19.6
