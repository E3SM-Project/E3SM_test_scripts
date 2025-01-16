#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=pm-cpu
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

declare -i fails=0
$RUNSCRIPT -t e3sm_eamxx_v1_medres --compiler=gnu --baseline-compare
