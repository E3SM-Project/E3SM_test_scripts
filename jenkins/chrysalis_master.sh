#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT --baseline-compare $RUNSCRIPT_FLAGS --pes-file $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml
