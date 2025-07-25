#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=pm-cpu
export SCREAM_MACHINE=$CIME_MACHINE
source $SCRIPTROOT/util/setup_common.sh

module load python/3.9
$RUNSCRIPT -t e3sm_prod --baseline-compare=yes --compiler=intel
