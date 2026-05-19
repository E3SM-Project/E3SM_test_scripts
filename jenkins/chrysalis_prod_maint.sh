#!/bin/bash -xe
# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
source $SCRIPTROOT/util/setup_common.sh

# Need an older e3sm unified due to maint-3.0 using older CIME
source /lcrc/soft/climate/e3sm-unified/load_e3sm_unified_1.10.0_chrysalis.sh

$RUNSCRIPT -t e3sm_prod $RUNSCRIPT_FLAGS --baseline-compare --pes-file $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml
