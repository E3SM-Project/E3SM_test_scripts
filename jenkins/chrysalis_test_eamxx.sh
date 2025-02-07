#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
source $SCRIPTROOT/util/setup_common.sh

cd $E3SMREPO/cime/scripts
./create_test SMS_Lh4.ne4_ne4.F2010-SCREAMv1.chrysalis_intel.eamxx-output-preset-1 --wait \
              --pesfile $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml
