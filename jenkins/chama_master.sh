#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=sandiatoss3
source $SCRIPTROOT/util/setup_common.sh

$RUNSCRIPT -t e3sm_developer

chmod -R g+rwX /nscratch/e3sm-jenkins/acme_scratch/sandiatoss3
chmod -R g+rwX /gpfs1/e3sm-jenkins/acme_scratch/sandiatoss3
