#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=compy
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT --compiler intel --baseline-compare=yes -t e3sm_prod

chmod -R g+rwX /compyfs/$USER/e3sm_scratch
