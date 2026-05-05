#!/bin/bash

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# top directory of all Polaris cronjob work
export POLARIS_CRON_ROOT="/lustre/orion/cli115/proj-shared/${USER}/polaris_scratch/cron"

mkdir -p $POLARIS_CRON_ROOT

# launch polaris cronjob
exec bash $HERE/polaris_cron.sh
