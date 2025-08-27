#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
source $SCRIPTROOT/util/setup_common.sh

cd $E3SMREPO/cime/scripts
./create_test e3sm_eamxx_mam4xx_lowres_debug --wait \
              --pesfile $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml
