# E3SM_test_scripts
Test scripts for cron and jenkins jobs

## How it works (for Jenkins jobs)

Make/modify a script in the `jenkins/` subdirectory of this repo. The script name
should be `$machine_$test.sh`. Every script must start with these three lines:

$machine should be a machine name in E3SM/cime_config/machines/config_machines.xml

The $test string is usually the name of the test suite or the branch it is run on (for developer and integration suites).
It may also include the compiler used if not default.
Examples:  "next", "homme", "landice", "next_intel", "e3sm_gpuacc"

```bash
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=$machine
source $SCRIPTROOT/util/setup_common.sh
```

where `$machine` is the E3SM machine name. If a `util/${machine}_setup.sh` file
exists, `setup_common.sh` will source it automatically.

## Example using chrysalis_next

Jenkins clones `E3SM` and `E3SM_test_scripts` into the top-level workspace directory:

```
E3SM/
E3SM_test_scripts/
```

It then runs the appropriate script for the job:

```bash
#!/bin/bash -xle
./E3SM_test_scripts/jenkins/chrysalis_next.sh
```

`chrysalis_next.sh` sets `CIME_MACHINE=chrysalis` and sources `setup_common.sh`,
which:

1. Locates the `E3SM` repo and sets `$E3SMREPO`
2. Finds `jenkins_script` inside E3SM and sets `$RUNSCRIPT`
3. Sources `util/chrysalis_setup.sh`, which loads the CIME environment, initializes
   lmod, sets `$PROJECT=e3sm`, and sets `$RUNSCRIPT_FLAGS` with the scratch root path

The script then runs:

```bash
$RUNSCRIPT -O master $RUNSCRIPT_FLAGS --baseline-compare \
  --pes-file $E3SMREPO/cime_config/testmods_dirs/config_pes_tests.xml
```

This invokes E3SM's `jenkins_script` with the default test suite for chrysalis,
comparing results against the `master` baseline.
