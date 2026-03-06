# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Purpose

This repo contains Jenkins CI and cron test scripts for the [E3SM](https://e3sm.org/) climate model. Scripts are run by Jenkins on HPC machines; they are not run locally.

## Workspace Layout (Jenkins)

Jenkins clones two repos side by side:
```
E3SM/
E3SM_test_scripts/
```
`setup_common.sh` auto-detects whether the E3SM repo is named `E3SM` or `ACME`. Override with `FORCE_REPO_PATH`.

## Script Structure

### Required boilerplate (every Jenkins script)
```bash
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=$machine
source $SCRIPTROOT/util/setup_common.sh
```

### Naming convention
`jenkins/${machine}_${test_or_branch}.sh`

### What `setup_common.sh` does
1. Locates the E3SM repo and sets `$E3SMREPO`
2. Finds `jenkins_script` inside E3SM and sets `$RUNSCRIPT`
3. Sources `util/${CIME_MACHINE}_setup.sh` if it exists (loads modules, sets `$RUNSCRIPT_FLAGS`, etc.)
4. If `$DEBUG` is set, `$RUNSCRIPT` becomes `echo <path>` (dry-run mode)

## Key Variables

| Variable | Description |
|---|---|
| `SCRIPTROOT` | Root of this repo |
| `CIME_MACHINE` | Machine name (e.g., `chrysalis`, `pm-cpu`, `frontier`) |
| `E3SMREPO` | Path to E3SM source repo |
| `RUNSCRIPT` | Path to `jenkins_script` inside E3SM |
| `RUNSCRIPT_FLAGS` | Extra flags, typically set in machine setup files |
| `SCREAM_MACHINE` | Set for SCREAM/EAMxx tests (often mirrors `CIME_MACHINE`) |

## Common `$RUNSCRIPT` Flags

| Flag | Purpose |
|---|---|
| `-t <suite>` | Test suite (e.g., `e3sm_prod`, `e3sm_eamxx_v1_medres`) |
| `--compiler=<compiler>` | Compiler (e.g., `intel`, `oneapi-ifx`, `craycray-mphipcc`, `craygnu-mphipcc`) |
| `-O <branch>` or `-b <branch>` | Baseline branch for comparisons |
| `--baseline-compare` | Enable baseline comparison |
| `--pes-file <path>` | PE layout XML file |
| `-j <N>` | Number of parallel jobs |
| `--jenkins-id <X>` | Identifier for scripts running multiple test suites |
| `--scratch-root <path>` | Override scratch directory |

## Adding a New Jenkins Script

1. Create `jenkins/${machine}_${test}.sh`
2. Add the 3-line boilerplate (setting `CIME_MACHINE` to the target machine)
3. Call `$RUNSCRIPT` with the appropriate flags
4. If the machine needs environment setup (modules, scratch paths), add or update `util/${machine}_setup.sh`

## Machine Setup Files (`util/`)

Each `util/${machine}_setup.sh` is machine-specific:
- Loads lmod/Python/modules needed by CIME
- Sets `$RUNSCRIPT_FLAGS` (e.g., `--scratch-root`)
- Sets `$PROJECT` if required by the batch system

## Alternative Test Runners

- `util/run_cime_tests.sh` - Runs CIME Python unit tests via cmake/ctest against CDash
- `util/run_e3sm_test.sh` + `util/run_e3sm_ctest/` - CMake+CTest project that tests `run_e3sm.template.csh` and posts results to CDash
