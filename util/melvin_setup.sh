
source /projects/sems/modulefiles/utils/sems-modules-init.sh
module load sems-env sems-python/2.7.9 sems-git sems-pylint

export http_proxy=http://sonproxy.sandia.gov:80
export RSYNC_PROXY=sonproxy.sandia.gov:80
export rsync_proxy=sonproxy.sandia.gov:80
export HTTPS_PROXY=http://sonproxy.sandia.gov:80
export https_proxy=http://sonproxy.sandia.gov:80
export HTTP_PROXY=http://sonproxy.sandia.gov:80
