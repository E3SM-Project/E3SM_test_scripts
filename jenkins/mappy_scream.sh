#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=mappy
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

declare -i fails=0
set +e
$RUNSCRIPT -t e3sm_eamxx --baseline-compare $@
if [[ $? != 0 ]]; then fails=$fails+1; fi
$RUNSCRIPT -t e3sm_eamxx_v1 --compiler=gnu9 --baseline-compare $@
if [[ $? != 0 ]]; then fails=$fails+1; fi

if [[ $fails > 0 ]]; then
    exit 1
fi
