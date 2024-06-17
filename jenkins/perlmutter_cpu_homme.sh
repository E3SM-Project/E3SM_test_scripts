#!/bin/bash -xe

exit_code=0

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=pm-cpu
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -O master $RUNSCRIPT_FLAGS -t homme_integration --compiler=intel || exit_code=1
$RUNSCRIPT -O master $RUNSCRIPT_FLAGS -t homme_integration --compiler=gnu || exit_code=1

exit $exit_code
