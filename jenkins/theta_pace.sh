#!/bin/bash -xle
# Purpose: Automate performance data upload to PACE
# Author: Sarat Sreepathi (sarat@ornl.gov)

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=theta
#source $SCRIPTROOT/util/setup_common.sh

# Performance archive directory on this platform
export PERF_ARCHIVE_DIR=/projects/ClimateEnergy_4/performance_archive
# Archives of old performance data on this platform
export OLD_PERF_ARCHIVE_DIR=${PERF_ARCHIVE_DIR}/../OLD_PERF

source $SCRIPTROOT/util/pace_archive.sh

