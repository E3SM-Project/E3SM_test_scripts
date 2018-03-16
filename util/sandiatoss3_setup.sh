
source /projects/sems/modulefiles/utils/sems-modules-init.sh
module load sems-env sems-python/2.7.9 sems-git

export PATH=/projects/ccsm/perl-5.10.1/bin:$PATH

export http_proxy=http://wwwproxy.sandia.gov:80
export RSYNC_PROXY=wwwproxy.sandia.gov:80
export rsync_proxy=wwwproxy.sandia.gov:80
export HTTPS_PROXY=http://wwwproxy.sandia.gov:80
export https_proxy=http://wwwproxy.sandia.gov:80
export HTTP_PROXY=http://wwwproxy.sandia.gov:80

