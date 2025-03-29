#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=compy
source $SCRIPTROOT/util/setup_common.sh

module load python/3.11.5
$RUNSCRIPT -j4 -t e3sm_eamxx_mam4xx_long_runtime --compiler intel
