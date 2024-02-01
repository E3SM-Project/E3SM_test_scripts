#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=frontier-scream-gpu
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -t e3sm_scream_v1_highres --compiler=crayclang-scream -b master --baseline-compare --check-throughput --check-memory --save-timing --ignore-namelists
