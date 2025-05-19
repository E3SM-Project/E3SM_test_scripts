#!/bin/bash

main() {

    #---------------------------------------------------------------
    # User-defined configuration
    #---------------------------------------------------------------
    #path to E3SM
    code_root="/global/homes/l/litzingj/E3SM"
    
    #machine to run the test on
    mach="pm-gpu"

    #compiler
    compiler=gnugpu

    #set resolution
    resolution=$1

    #set timestep
    timestep=Ld5

    #set data destination
    data_dest="/global/homes/l/litzingj/performance_data/${timestep}"

    #set shared data destination
    share_dest="/global/cfs/cdirs/e3sm/www/litz372/performance_data"

    #load modules
    module load cray-python/3.11.7

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    #TODO: 
    /global/homes/l/litzingj/E3SM_test_scripts/jenkins/mam4xx_compare_performance.sh -r $resolution -c $compiler -t $timestep -m $mach -p $code_root -d $data_dest -s $share_dest

}

#--------------------------
# Start the script
#--------------------------
main $1
