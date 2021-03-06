
if [ -z "$SEMS_MODULEFILES_ROOT" ]; then
    source /projects/sems/modulefiles/utils/sems-modules-init.sh
fi

# We only need cmake here because mappy run cime standalone tests which
# do not load the CIME env before running cmake
module load sems-git/2.10.1 sems-cmake/3.19.1
export PATH=/ascldap/users/jgfouca/packages/Python-3.8.5/bin:$PATH

export http_proxy=http://proxy.sandia.gov:80
export RSYNC_PROXY=proxy.sandia.gov:80
export rsync_proxy=proxy.sandia.gov:80
export HTTPS_PROXY=http://proxy.sandia.gov:80
export https_proxy=http://proxy.sandia.gov:80
export HTTP_PROXY=http://proxy.sandia.gov:80
