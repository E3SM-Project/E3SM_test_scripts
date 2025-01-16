#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=quartz
source $SCRIPTROOT/util/setup_common.sh

declare -i fails=0
set +e
$RUNSCRIPT -t e3sm_eamxx -b master
if [[ $? != 0 ]]; then fails=$fails+1; fi
$RUNSCRIPT -t e3sm_eamxx_v1 -b master
if [[ $? != 0 ]]; then fails=$fails+1; fi

if [[ $fails > 0 ]]; then
    exit 1
fi
