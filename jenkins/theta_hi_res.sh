#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=theta
source $SCRIPTROOT/util/setup_common.sh

DATE_STAMP=$(date "+%Y-%m-%d_%H%M%S")

$FORCE_REPO_PATH/cime/scripts/Tools/jenkins_generic_job -j 4 --submit-to-cdash -t e3sm_hi_res >> THETA_JENKINS_$DATE_STAMP 2>&1
