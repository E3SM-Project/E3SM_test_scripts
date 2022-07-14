#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=crusher
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j 4 -t cime_tiny $1 || exit 0
