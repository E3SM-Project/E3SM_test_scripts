#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=ascent
source $SCRIPTROOT/util/setup_common.sh

export http_proxy=http://proxy.ccs.ornl.gov:3128/ 
export https_proxy=https://proxy.ccs.ornl.gov:3128/

$RUNSCRIPT -j 4 -t e3sm_integration --compiler ibmgpu
