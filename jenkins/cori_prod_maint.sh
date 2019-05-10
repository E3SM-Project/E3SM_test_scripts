#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=cori-knl
source $SCRIPTROOT/util/setup_common.sh

cd $E3SMREPO && git submodule update --init
cd -
$RUNSCRIPT -j 2 -t e3sm_prod -O master --baseline-compare=yes
