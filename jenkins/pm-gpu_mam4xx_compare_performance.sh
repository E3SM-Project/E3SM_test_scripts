#!/bin/bash

main() {

    #---------------------------------------------------------------
    # User-defined configuration
    #---------------------------------------------------------------
    #path to E3SM
    code_root="/pscratch/sd/e/e3smtest/jenkins/workspace/ACME_Perlmutter_mam4xx_compare_performance/E3SM"
    #code_root="/global/cfs/projectdirs/e3sm/litzingj/E3SM"
    #boolean if E3SM git should fetch and reset 
    hard_reset_E3SM=false 
    
    #machine to run the test on
    mach="pm-gpu"

    #compiler
    compiler=gnugpu

    #set resolution
    resolution=$1

    #set the length of the simulation (ie Ld5 for 5 days or Ln5 for 5 timesteps)
    simulation_length=Ld5

    #directory for all the past and current data
    data_dest="/global/cfs/projectdirs/e3sm/litzingj/performance_data/${simulation_length}"

    #path where the latest time series plot is saved, accessible to the whole project
    share_dest="/global/cfs/cdirs/e3sm/www/litz372/performance_data"

    #url where the plot will be available - based on the share_dest
    share_url="https://portal.nersc.gov/cfs/e3sm/litz372/performance_data/performance_comp_${resolution}_${simulation_length}.png"

    #load modules
    module load cray-python/3.11.7
    source ${code_root}/../venv/bin/activate

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    #TODO: 
    /global/cfs/projectdirs/e3sm/litzingj/E3SM_test_scripts/jenkins/mam4xx_compare_performance.sh -r $resolution -c $compiler -t $simulation_length -m $mach -p $code_root -f $hard_reset_E3SM -d $data_dest -s $share_dest -u $share_url

}

#--------------------------
# Start the script
#--------------------------
main $1
