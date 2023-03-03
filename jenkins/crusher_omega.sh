#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=crusher
export FORCE_REPO_PATH=Omega
source $SCRIPTROOT/util/setup_common.sh

exit_code=0
$RUNSCRIPT -j 4 -t e3sm_gpuacc --compiler crayclanggpu || exit_code=1

exit $exit_code
