#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=anvil
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j 4 --compiler gnu --pes-file $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml

source $SCRIPTROOT/util/anvil_postrun.sh
