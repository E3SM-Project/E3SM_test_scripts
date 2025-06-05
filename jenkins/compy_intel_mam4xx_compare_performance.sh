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

    #set the length of the simulation (ie Ld5 for 5 days or Ln5 for 5 timesteps) 
    simulation_length=Ld5

    #directory for all the past and current data
    data_dest="/qfs/projects/eagles/litz372/performance_data/${simulation_length}"

    #path where the latest time series plot is saved, accessible to the whole project
    share_dest="/compyfs/www/litz372/performance_data"
    
    #url where the plot will be available - based on the share_dest
    share_url="https://compy-dtn.pnl.gov/litz372/performance_data/performance_comp_${resolution}_${simulation_length}.png"

    #load modules
    source /etc/profile.d/modules.sh
    module load python/3.11.5
    source ${code_root}/../.venv/bin/activate

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    #TODO: 
    /compyfs/litz372/e3sm_scratch/performance_testing/E3SM_test_scripts/jenkins/mam4xx_compare_performance.sh -r $resolution -c $compiler -t $simulation_length -m $mach -p $code_root -d $data_dest -s $share_dest -u $share_url

}


#--------------------------
# Start the script
#--------------------------
main $1
