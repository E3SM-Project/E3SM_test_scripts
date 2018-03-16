#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=blues
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j 4
