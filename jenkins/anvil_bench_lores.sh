#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=anvil
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -j 2 -t e3sm_bench_lores --compiler=intel -O master --baseline-compare --check-throughput --check-memory --save-timing --ignore-namelists --ignore-diffs

source $SCRIPTROOT/util/anvil_postrun.sh
