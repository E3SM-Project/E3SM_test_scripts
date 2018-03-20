#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=theta
source $SCRIPTROOT/util/setup_common.sh

cd ../ACME-theta
git checkout next
git fetch
git reset --hard origin/next
git submodule update --init
cd -

DATE_STAMP=$(date "+%Y-%m-%d_%H%M%S")

../ACME-theta/cime/scripts/Tools/jenkins_generic_job -j 4 --submit-to-cdash -t e3sm_integration >& THETA_JENKINS_$DATE_STAMP || echo moving_on

cd ../ACME-theta
git checkout master
git fetch
git reset --hard origin/master
git submodule update --init
cd -

DATE_STAMP=$(date "+%Y-%m-%d_%H%M%S")

../ACME-theta/cime/scripts/Tools/jenkins_generic_job -j 4 --submit-to-cdash -t e3sm_hi_res >> THETA_JENKINS_$DATE_STAMP 2>&1
