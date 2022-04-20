#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT --baseline-compare

# OpenMPI creates .loc/.lock files which might stay on after aborted file close, force clean them
find /lcrc/group/e3sm/data/ -name "*.loc*" -exec rm -f {} \;
