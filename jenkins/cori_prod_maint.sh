#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=cori-knl
source $SCRIPTROOT/util/setup_common.sh

# deactivate cime_env for python 2
conda deactivate
module load python/2.7-anaconda-5.2


cd $E3SMREPO && git submodule update --init --recursive
cd -
$RUNSCRIPT -j 2 -t e3sm_prod --baseline-compare=yes
