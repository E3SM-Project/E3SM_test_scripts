#!/bin/bash

main() {

    #---------------------------------------------------------------
    # User-defined configuration
    #---------------------------------------------------------------
    #path to E3SM
    code_root="/compyfs/litz372/e3sm_scratch/performance_testing/E3SM"
    
    #machine to run the test on
    mach="compy"

    #compiler
    compiler=intel

    #set resolution
    resolution=$1

    #set timestep
    timestep=5

    #set data destination
    data_dest="/qfs/projects/eagles/litz372/performance_data"

    #set shared data destination
    share_dest="/compyfs/www/litz372/performance_data"

    #load modules
    source /etc/profile.d/modules.sh
    module load python/3.11.5

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    #TODO: 
    /compyfs/litz372/e3sm_scratch/performance_testing/E3SM_test_scripts/jenkins/mam4xx_compare_performance.sh -r $resolution -c $compiler -t $timestep -m $mach -p $code_root -d $data_dest $share_dest

}


#--------------------------
# Start the script
#--------------------------
main $1
