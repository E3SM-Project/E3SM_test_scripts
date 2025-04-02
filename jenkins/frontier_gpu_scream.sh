#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=frontier
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

exit_code=0
$RUNSCRIPT -t e3sm_eamxx_v1_medres     --compiler=craycray-mphipcc -b master --jenkins-id A || exit_code=1
$RUNSCRIPT -t e3sm_eamxx_v1_medres     --compiler=craygnu-hipcc    -b master --jenkins-id B || exit_code=1
$RUNSCRIPT -t e3sm_eamxx_mam4xx_lowres --compiler=craygnu-hipcc    -b master --jenkins-id C || exit_code=1


exit $exit_code
