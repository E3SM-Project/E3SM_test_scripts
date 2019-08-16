# E3SM_test_scripts
Test scripts for cron and jenkins jobs

How it works (for Jenkins jobs):

Make/modify a script in the jenkins subdirectory of this repo. The script name 
should be `$machine_$branch_$test`. The first code block for all the 
scripts should be:

```bash
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=$machine
source $SCRIPTROOT/util/setup_common.sh
```

where `$machine` is the E3SM machine for the test, and the lines below this 
block are the actual test.

Note: If a `util/$machine_setup.sh` file exists, it will also be sourced.

The test process:

Jenkins will clone  `E3SM` and `E3SM_test_scripts` into the top level workspace 
directory:

```bash
% ls
ACME
E3SM_test_scripts
```
It will then just run the appropriate script for the job, for example, this is 
skybridge job:

```bash
#!/bin/bash -xle
./E3SM_test_scripts/jenkins/skybridge_next.sh
```