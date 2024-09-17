#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=mappy
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -O master --baseline-compare
