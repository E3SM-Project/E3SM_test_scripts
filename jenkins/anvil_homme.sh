#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=anvil
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -O master $RUNSCRIPT_FLAGS -t homme_integration
