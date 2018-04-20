#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=edison
source $SCRIPTROOT/util/setup_common.sh

source $SCRIPTROOT/util/run_e3sm_test.sh
