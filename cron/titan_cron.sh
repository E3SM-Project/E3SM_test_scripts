#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=titan
source $SCRIPTROOT/util/setup_common.sh

/bin/rm -rf ~/acme_scratch/cli115/*

cd ACME
git checkout next
git fetch
git reset --hard origin/next
git submodule update --init

$RUNSCRIPT --scratch-root=$PROJWORK/cli115/$USER -j 4 -t acme_prod
$RUNSCRIPT --scratch-root=$PROJWORK/cli115/$USER -j 4

chmod a+rX -R $PROJWORK/cli115/$USER
