
source /projects/sems/modulefiles/utils/sems-archive-modules-init.sh

module load sems-git

export PATH=/ascldap/users/jgfouca/packages/Python-3.8.5/bin:$PATH
export PATH=/projects/ccsm/perl-5.10.1/bin:$PATH

export http_proxy=http://proxy.sandia.gov:80
export RSYNC_PROXY=proxy.sandia.gov:80
export rsync_proxy=proxy.sandia.gov:80
export HTTPS_PROXY=http://proxy.sandia.gov:80
export https_proxy=http://proxy.sandia.gov:80
export HTTP_PROXY=http://proxy.sandia.gov:80

