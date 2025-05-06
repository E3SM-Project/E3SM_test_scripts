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
    resolution=ne4pg2_ne4pg2

    #set timestep
    timestep=5

    #set data destination
    data_dest="/global/homes/l/litzingj/performance_data"

    #load modules
    module load cray-python/3.11.7

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    #TODO: 
    ./mam4xx_compare_performance.sh -r $resolution -c $compiler -t $timestep -m $mach -p $code_root -d $data_dest

}

#--------------------------
# Start the script
#--------------------------
main
