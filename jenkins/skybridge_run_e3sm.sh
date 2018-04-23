#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=sandiatoss3
source $SCRIPTROOT/util/setup_common.sh

git config --global http.proxy $http_proxy

source $SCRIPTROOT/util/run_e3sm_test.sh
