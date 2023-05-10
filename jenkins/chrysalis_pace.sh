#!/bin/bash -xe
# Purpose: Automate performance data upload to PACE
# Author: Sarat Sreepathi (sarat@ornl.gov)

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=chrysalis
#source $SCRIPTROOT/util/setup_common.sh

# Performance archive directory on this platform
export PERF_ARCHIVE_DIR=/lcrc/group/e3sm/PERF_Chrysalis/performance_archive
# Archives of old performance data on this platform
export OLD_PERF_ARCHIVE_DIR=${PERF_ARCHIVE_DIR}/../OLD_PERF
# Following tag is used by the Perl script in naming the perf. archive directory
export PROJ_SPACE_TAG=e3sm

module load anaconda3/2020.11
export PACE_PYTHON3=1
source $SCRIPTROOT/util/pace_archive.sh

