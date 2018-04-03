umask 002
export E3SMREPO=$SCRIPTROOT/../${FORCE_REPO_PATH:-ACME}
export CIME_MODEL=e3sm
if [ -z "$DEBUG" ]; then
    export RUNSCRIPT=$E3SMREPO/cime/scripts/Tools/jenkins_script
else
    export RUNSCRIPT="echo $E3SMREPO/cime/scripts/Tools/jenkins_script"
fi
chmod -R a+rX $E3SMREPO

# Clear stale pyc files
/bin/rm $(find $E3SMREPO -name "*.pyc")

machine_custom_setup=$SCRIPTROOT/util/${CIME_MACHINE}_setup.sh
if [ -e $machine_custom_setup ]; then
    source $machine_custom_setup
fi
