#!/bin/bash

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# top directory of all Polaris cronjob work
export POLARIS_CRON_ROOT="$PSCRATCH/polaris_scratch/cron/pm-cpu"

mkdir -p $POLARIS_CRON_ROOT

# launch polaris cronjob
exec bash $HERE/polaris_cron.sh
