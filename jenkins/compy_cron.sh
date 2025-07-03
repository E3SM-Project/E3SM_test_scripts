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
    resolution=ne30pg2_ne30pg2

    #set the length of the simulation (ie Ld5 for 5 days or Ln5 for 5 timesteps) 
    simulation_length=Ld5

    #directory for all the past and current data
    data_dest="/qfs/projects/eagles/litz372/performance_data/${simulation_length}"

    #path where the latest time series plot is saved, accessible to the whole project
    share_dest="/compyfs/www/litz372/performance_data"
    
    #url where the plot will be available - based on the share_dest
    share_url_ne30="https://compy-dtn.pnl.gov/litz372/performance_data/performance_comp_${resolution}_${simulation_length}.png"

    #load modules
    source /etc/profile.d/modules.sh
    module load python/3.11.5

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    #---------------------------------------------------------------
    # RUN NE30 SIMULATION 
    #---------------------------------------------------------------

    #/compyfs/litz372/e3sm_scratch/performance_testing/E3SM_test_scripts/jenkins/mam4xx_compare_performance.sh -r $resolution -c $compiler -t $simulation_length -m $mach -p $code_root -d $data_dest -s $share_dest -u $share_url_ne30

    #---------------------------------------------------------------
    # RUN NE4 SIMULATION 
    #---------------------------------------------------------------

    resolution=ne4pg2_ne4pg2
    share_url_ne4="https://compy-dtn.pnl.gov/litz372/performance_data/performance_comp_${resolution}_${simulation_length}.png"
    #/compyfs/litz372/e3sm_scratch/performance_testing/E3SM_test_scripts/jenkins/mam4xx_compare_performance.sh -r $resolution -c $compiler -t $simulation_length -m $mach -p $code_root -d $data_dest -s $share_dest -u $share_url_ne4

    #---------------------------------------------------------------
    # RUN PERFORMANCE BREAKDOWN 
    #---------------------------------------------------------------

    #/compyfs/litz372/e3sm_scratch/compare_model_performance/E3SM_test_scripts/jenkins/compy_model_performance.sh

    #---------------------------------------------------------------
    # APPEND LINE GRAPHS TO BREAKDOWN 
    #---------------------------------------------------------------

    #plot line in dash comp
    source ${code_root}/../.venv/bin/activate
    output_graph=${share_dest}/../compare_performance/plot.html
    echo $share_url_ne4 
    echo $share_url_ne30
    echo $output_graph
    python3 plot_html.py -i ${share_url_ne4} -o ${output_graph} 
    python3 plot_html.py -i ${share_url_ne30} -o ${output_graph} 

}

#--------------------------
# Start the script
#--------------------------
main 
