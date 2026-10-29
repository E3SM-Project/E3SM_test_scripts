#!/bin/bash -xe

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=mappy
source $SCRIPTROOT/util/setup_common.sh

SUITE=e3sm_developer                       # machine default for mappy
SCRATCH=$HOME/acme/scratch                 # CIME_OUTPUT_ROOT, or your own
BASELINE=master
BRANCH=next
BUILD_CPU_COUNT=32
# same pattern jenkins_generic_job uses: J<Baseline><Suite-no-e3sm_>, then a timestamp
S=${SUITE#e3sm_}; TESTID=J${BRANCH^}${S^}$(date +%y%m%d_%H%M%S)
TESTS_FAILED_RC=$(PYTHONPATH=$E3SMREPO/cime python3 -c \
  'from CIME.utils import TESTS_FAILED_ERR_CODE as c; print(c)')

# Unset -e, since we don't want to crap out before running RUNSCRIPT (the jenkins_script in E3SM)
# just b/c one or more tests failed one of the test phases. E.g., a FAIL in case.build would make
# create_test return cime's $TEST_FAILED_ERR_CODE.
set +e
salloc -c $BUILD_CPU_COUNT -t 04:00:00 env -u SLURM_CPUS_PER_TASK -u SLURM_JOB_ID \
  $E3SMREPO/cime/scripts/create_test $SUITE --test-root $SCRATCH/J -t $TESTID \
  -c -b $BASELINE --proc-pool $BUILD_CPU_COUNT
rc=$?

# Re-set -e
set -e
if [ $rc -ne 0 ] && [ $rc -ne $TESTS_FAILED_RC ]; then
  echo "create_test/salloc failed: $rc"; exit $rc;
fi

$RUNSCRIPT --use-existing-test-id $TESTID -t $SUITE -r $SCRATCH -b $BRANCH --no-submit --no-update-success
