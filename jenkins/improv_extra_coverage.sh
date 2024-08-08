#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=improv
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j4 -t e3sm_extra_coverage
