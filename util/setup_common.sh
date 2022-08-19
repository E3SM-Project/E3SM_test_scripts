umask 002

if [ -z "$FORCE_REPO_PATH" ]; then
  if [ -d $SCRIPTROOT/../E3SM ]; then
    FOUND_REPO_NAME=E3SM
  elif [ -d $SCRIPTROOT/../ACME ]; then
    FOUND_REPO_NAME=ACME
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

if [ -f $E3SMREPO/cime/CIME/Tools/jenkins_script ]; then
  PATH_TO_JENKINS=$E3SMREPO/cime/CIME/Tools/jenkins_script
else
  PATH_TO_JENKINS=$E3SMREPO/cime/scripts/Tools/jenkins_script
fi

if [ -z "$DEBUG" ]; then
  export RUNSCRIPT=$PATH_TO_JENKINS
else
  export RUNSCRIPT="echo $PATH_TO_JENKINS"
fi
chmod -R a+rX $E3SMREPO || echo "Some chmods failed"

# Clear stale pyc files
PYC_CACHES=$(find $E3SMREPO -name "*.pyc")
if [[ ! -z "$PYC_CACHES" ]]; then
   /bin/rm $PYC_CACHES || echo "Some pyc removals failed"
fi

machine_custom_setup=$SCRIPTROOT/util/${CIME_MACHINE}_setup.sh
if [ -e $machine_custom_setup ]; then
  source $machine_custom_setup
fi
