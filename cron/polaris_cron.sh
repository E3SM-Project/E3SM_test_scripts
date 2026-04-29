#!/bin/bash

# Configuration
export POLARIS_ROOT=$POLARIS_CRON_ROOT/polaris
#REMOTE_URL="https://github.com/E3SM-Project/polaris.git"
#BRANCH="main"
REMOTE_URL="https://github.com/grnydawn/polaris.git"
BRANCH="ykim/copilot/cron-scripts"

rm -rf ${POLARIS_ROOT}

git clone -b "$BRANCH" "$REMOTE_URL" "$POLARIS_ROOT"
cd "$POLARIS_ROOT" || exit

# Update specific submodules recursively
echo "Updating submodules..."
git submodule update --init --recursive jigsaw-python
git submodule update --init e3sm_submodules/Omega
pushd e3sm_submodules/Omega
git submodule update --init --recursive externals/ekat externals/scorpio cime components/omega/external
popd

# Launch the final script with all passed arguments
LAUNCH_SCRIPT="$POLARIS_ROOT/cron-scripts/launch_all.sh"

if [ -f "$LAUNCH_SCRIPT" ]; then
    echo "Launching: $LAUNCH_SCRIPT $*"
    exec bash "$LAUNCH_SCRIPT" "$@"
else
    echo "Error: Launch script not found at $LAUNCH_SCRIPT"
    exit 1
fi
