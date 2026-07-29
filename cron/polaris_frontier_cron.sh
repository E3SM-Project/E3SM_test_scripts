#!/bin/bash

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

source /etc/bash.bashrc

# top directory of all Polaris cronjob work
export POLARIS_CRON_ROOT="/lustre/orion/cli115/proj-shared/$USER/polaris_scratch/cron"

export all_proxy=socks://proxy.ccs.ornl.gov:3128/
export ftp_proxy=ftp://proxy.ccs.ornl.gov:3128/
export http_proxy=http://proxy.ccs.ornl.gov:3128/
export https_proxy=http://proxy.ccs.ornl.gov:3128/
export no_proxy='localhost,127.0.0.0/8,*.ccs.ornl.gov'

mkdir -p $POLARIS_CRON_ROOT

# launch polaris cronjob
exec bash $HERE/polaris_cron.sh
