#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

declare -i fails=0
set +e
$RUNSCRIPT -j 4 -t e3sm_eamxx_mam4xx_lowres_debug $RUNSCRIPT_FLAGS --baseline-compare --pes-file $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml $@
if [[ $? != 0 ]]; then fails=$fails+1; fi

if [[ $fails > 0 ]]; then
    exit 1
fi
