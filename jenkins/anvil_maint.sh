#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=anvil
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j 4 e3sm_production --compiler intel --baseline-compare=yes

source $SCRIPTROOT/util/anvil_postrun.sh
