#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=crusher-scream-gpu
export FORCE_REPO_PATH=scream
source $SCRIPTROOT/util/setup_common.sh

exit_code=0
$RUNSCRIPT -j 4 -t e3sm_eamxx_v1_long_crusher --compiler=crayclang-scream -b master || exit_code=1

$RUNSCRIPT -j 4 -t e3sm_eamxx_v1 --compiler=crayclang-scream -b master || exit_code=1

exit $exit_code
