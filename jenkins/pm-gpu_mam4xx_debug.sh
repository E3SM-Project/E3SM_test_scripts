#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=pm-gpu
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

exit_code=0
$RUNSCRIPT -t e3sm_eamxx_mam4xx_lowres_debug --compiler=gnugpu --baseline-compare || exit_code=1

exit $exit_code
