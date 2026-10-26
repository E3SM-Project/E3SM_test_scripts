#!/bin/bash

# nohup_wrapper.sh - run a command so it survives a SIGHUP (e.g. a dropped
# network/SSH connection to the Jenkins agent) while still streaming live
# output to the console and propagating the real exit code.
#
# Usage:
#   $SCRIPTROOT/util/nohup_wrapper.sh <command> [args...]
#
# Example (in a jenkins/ script):
#   $SCRIPTROOT/util/nohup_wrapper.sh $RUNSCRIPT -t e3sm_eamxx_extra_large \
#     --compiler=gnugpu --baseline-compare
#
# The wrapped command runs under nohup so it ignores SIGHUP. Its stdout/stderr
# are captured to a log file that is tailed in the foreground, so the Jenkins
# console still shows progress. When the wrapped command exits, this wrapper
# exits with the same status.

if [ $# -eq 0 ]; then
  echo "nohup_wrapper.sh: no command given" >&2
  exit 2
fi

logfile="${NOHUP_WRAPPER_LOG:-nohup_wrapper.$$.$(date +%Y%m%d_%H%M%S).log}"
echo "nohup_wrapper.sh: running '$*'"
echo "nohup_wrapper.sh: output is also logged to $logfile"

# Launch under nohup so the command ignores SIGHUP if the controlling
# terminal/connection goes away. Keep stdin detached from any terminal.
nohup "$@" > "$logfile" 2>&1 < /dev/null &
cmd_pid=$!

# Stream the log to the console, stopping automatically when the command exits.
tail -n +1 -F --pid=$cmd_pid "$logfile" &
tail_pid=$!

# Forward common termination signals to the wrapped command so Jenkins aborts
# still stop the real work.
trap 'kill -TERM "$cmd_pid" 2>/dev/null' TERM INT

# Wait for the wrapped command and capture its real exit status.
wait "$cmd_pid"
rc=$?

# Make sure the remaining log is flushed, then stop the tail.
wait "$tail_pid" 2>/dev/null
kill "$tail_pid" 2>/dev/null

echo "nohup_wrapper.sh: command exited with status $rc"
exit $rc
