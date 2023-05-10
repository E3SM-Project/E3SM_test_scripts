#!/bin/bash -xe
# Purpose: Automate performance data upload to PACE
# Author: Sarat Sreepathi (sarat@ornl.gov)

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=cori
#source $SCRIPTROOT/util/setup_common.sh

# Performance archive directory on this platform
PERF_ARCHIVE_DIR=/global/cfs/cdirs/e3sm/performance_archive
# Archives of old performance data on this platform
export OLD_PERF_ARCHIVE_DIR=${PERF_ARCHIVE_DIR}/../OLD_PERF
# Following tag is used by the Perl script in naming the perf. archive directory
export PROJ_SPACE_TAG=e3sm

export PACE_PYTHON3=1
source $SCRIPTROOT/util/pace_archive.sh

