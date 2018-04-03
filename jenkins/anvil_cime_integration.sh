#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=anvil
source $SCRIPTROOT/util/setup_common.sh

cd $E3SMREPO
/bin/rm -rf cime
git clone git@github.com:ESMCI/cime.git

/bin/rm -rf /lcrc/group/acme/acmetest/acme_scratch/*cime_test*

./cime/scripts/create_test --machine anvil PET_Ln9_PS.ne30_oECv3_ICG.A_WCYCL1850S -t cime_test

./cime/scripts/Tools/wait_for_tests /lcrc/group/acme/acmetest/acme_scratch/*cime_test*/TestStatus -b cime_integration_test -g Experimental
