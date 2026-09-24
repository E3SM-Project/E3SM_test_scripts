#!/bin/bash

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# top directory of all Polaris cronjob work
export POLARIS_CRON_ROOT="$PSCRATCH/polaris_scratch/cron/pm-gpu"

mkdir -p $POLARIS_CRON_ROOT

if [[ ! -z "${SLURM_MEM_PER_CPU}" ]]; then
unset SLURM_MEM_PER_CPU
unset SLURM_OPEN_MODE
fi

# launch polaris cronjob
exec bash $HERE/polaris_cron.sh -m pm-gpu
