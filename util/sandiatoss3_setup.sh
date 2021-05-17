
if [ -z "$SEMS_MODULEFILES_ROOT" ]; then
    source /projects/sems/modulefiles/utils/sems-modules-init.sh
fi

module load sems-git

if [[ $GIT_BRANCH == *master* ]]; then
    module load sems-python/2.7.9
else
    module load sems-python/3.5.2
fi
module load sems-pylint/1.5.4/base

export PATH=/projects/ccsm/perl-5.10.1/bin:$PATH

export http_proxy=http://wwwproxy.sandia.gov:80
export RSYNC_PROXY=wwwproxy.sandia.gov:80
export rsync_proxy=wwwproxy.sandia.gov:80
export HTTPS_PROXY=http://wwwproxy.sandia.gov:80
export https_proxy=http://wwwproxy.sandia.gov:80
export HTTP_PROXY=http://wwwproxy.sandia.gov:80

