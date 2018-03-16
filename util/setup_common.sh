umask 002
export E3SMREPO=$SCRIPTROOT/../ACME
export RUNSCRIPT=$E3SMREPO/cime/scripts/Tools/jenkins_script
chmod -R a+rX E3SMREPO

machine_custom_setup=$SCRIPTROOT/util/${CIME_MACHINE}_setup.sh
if [ -f $machine_custom_setup ]; then
    source $machine_custom_setup
fi
