#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=pm-gpu
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

# Run under nohup so a dropped network/SSH connection (SIGHUP) does not kill
# this very long running job. See util/nohup_wrapper.sh.
$SCRIPTROOT/util/nohup_wrapper.sh $RUNSCRIPT -t e3sm_eamxx_extra_large --compiler=gnugpu --baseline-compare
