
#!/bin/bash -xle

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=compy
source $SCRIPTROOT/util/setup_common.sh

# deactivate cime_env for python 2
conda deactivate
module load python/2.7-anaconda-5.2

$RUNSCRIPT --compiler pgi --baseline-compare=yes -t e3sm_bgcprod

chmod -R g+rwX /compyfs/$USER/e3sm_scratch
