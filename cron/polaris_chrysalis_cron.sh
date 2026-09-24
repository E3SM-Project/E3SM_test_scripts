#!/bin/bash

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# top directory of all Polaris cronjob work
export POLARIS_CRON_ROOT="/lcrc/group/e3sm/$USER/scratch/cron"

mkdir -p $POLARIS_CRON_ROOT

# launch polaris cronjob
exec bash $HERE/polaris_cron.sh
