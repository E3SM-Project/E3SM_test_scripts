#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=anvil
source $SCRIPTROOT/util/setup_common.sh

exit_code=0
$RUNSCRIPT -j 4 -t e3sm_prod $RUNSCRIPT_FLAGS --compiler intel --baseline-compare --pes-file $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml || exit_code=1

source $SCRIPTROOT/util/anvil_postrun.sh

exit $exit_code
