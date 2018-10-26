#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=cori-knl
source $SCRIPTROOT/util/setup_common.sh

module load python/2.7-anaconda-5.2
$RUNSCRIPT -j 2 -t e3sm_atm_nbfb -O master --baseline-compare=yes
