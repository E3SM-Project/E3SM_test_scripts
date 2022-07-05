#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=jlse
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j 4 -t e3sm_gpuomp $1 || exit 0
