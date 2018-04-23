umask 002

if [ -z "$FORCE_REPO_PATH" ]; then
  if [ -d $SCRIPTROOT/../ACME ]; then
    FOUND_REPO_NAME=ACME
  elif [ -d $SCRIPTROOT/../E3SM ]; then
    FOUND_REPO_NAME=E3SM
  else
    # Not certain this is the best way to handle this...
    echo "Could not find the E3SM repo"
    exit 1
  fi
  export E3SMREPO=$SCRIPTROOT/../${FOUND_REPO_NAME}
else
  export E3SMREPO=$SCRIPTROOT/../${FORCE_REPO_PATH}
fi

export CIME_MODEL=e3sm
if [ -z "$DEBUG" ]; then
  export RUNSCRIPT=$E3SMREPO/cime/scripts/Tools/jenkins_script
else
  export RUNSCRIPT="echo $E3SMREPO/cime/scripts/Tools/jenkins_script"
fi
chmod -R a+rX $E3SMREPO || echo "Some chmods failed"

# Clear stale pyc files
/bin/rm $(find $E3SMREPO -name "*.pyc") || echo "Some pyc removals failed"

machine_custom_setup=$SCRIPTROOT/util/${CIME_MACHINE}_setup.sh
if [ -e $machine_custom_setup ]; then
  source $machine_custom_setup
fi
