#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=frontier
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -t e3sm_eamxx_v1_medres --compiler=craycray-mphipcc -b master --jenkins-id A
$RUNSCRIPT -t e3sm_eamxx_v1_medres --compiler=craygnu-hipcc -b master --jenkins-id B
