# E3SM_test_scripts
Test scripts for cron and jenkins jobs

How it works (for Jenkins jobs):

Make/modify a script in the jenkins subdirectory of this repo. The script name should be $machine_$branch_$test.
The first code block for all the scripts should be:

export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=$machine
source $SCRIPTROOT/util/setup_common.sh

... where $machine is the e3sm machine for the test.

The lines below this block are the actual test.

If a util/$machine_setup.sh file exists, it will also be sourced.

The test process:

Jenkins will clone E3SM and E3SM_test_scripts into the top level workspace directory:
% ls
ACME
E3SM_test_scripts

It will then just run the appropriate script for the job, for example, this is skybridge job:

#!/bin/bash -xle
./E3SM_test_scripts/jenkins/skybridge_next.sh
