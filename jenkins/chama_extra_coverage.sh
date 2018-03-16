#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=sandiatoss3
source $SCRIPTROOT/utils/setup_common.sh

$RUNSCRIPT -j4 -t e3sm_extra_coverage --baseline-compare=no
