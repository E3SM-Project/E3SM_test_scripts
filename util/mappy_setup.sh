
# This should be done upon login
#source /projects/sems/modulefiles/utils/sems-modules-init.sh

# We only need cmake here because mappy run cime standalone tests which
# do not load the CIME env before running cmake
module purge
module load sems-git/2.42.0 sems-cmake/3.27.9

export http_proxy=http://proxy.sandia.gov:80
export RSYNC_PROXY=proxy.sandia.gov:80
export rsync_proxy=proxy.sandia.gov:80
export HTTPS_PROXY=http://proxy.sandia.gov:80
export https_proxy=http://proxy.sandia.gov:80
export HTTP_PROXY=http://proxy.sandia.gov:80
