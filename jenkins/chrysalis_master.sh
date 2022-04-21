#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
source $SCRIPTROOT/util/setup_common.sh

source $SCRIPTROOT/util/chrysalis_clean_locks.sh

$RUNSCRIPT --baseline-compare

source $SCRIPTROOT/util/chrysalis_clean_locks.sh
