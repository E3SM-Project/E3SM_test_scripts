#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=cori-knl
source $SCRIPTROOT/util/setup_common.sh

# Unload python module from:
# $SCRIPTROOT/util/setup_common.sh --> $SCRIPTROOT/util/${CIME_MACHINE}_setup.sh
module unload python/2.7-anaconda-5.2

# Get e3sm_simple conda env
source /global/project/projectdirs/acme/software/anaconda_envs/load_latest_e3sm_simple.sh

$RUNSCRIPT -j 2 -t e3sm_atm_nbfb -O master --baseline-compare=yes
