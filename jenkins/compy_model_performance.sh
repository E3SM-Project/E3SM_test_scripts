#!/bin/bash

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Description:
#   This script automates the process of comparing model performance between master and development branches of E3SM.
#
# Usage:
#   Customize the user input section below before running the script.
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

main() {

    #---------------------------------------------------------------
    # User-defined configuration
    #---------------------------------------------------------------

    # Perlmutter
    # machine=pm-cpu 
    # compiler=gnu 
    # project=e3sm 
    # workdir=/pscratch/sd/m/meng/compare_model_performance 
    # plotdir=/global/cfs/cdirs/e3sm/www/meng/compare_performance  # make sure this a www in your Community directory to check the plot as a html page
    # html_address=https://portal.nersc.gov/cfs/e3sm/meng/compare_performance
    # module load python 

    # Compy
    machine=compy
    compiler=intel
    project=e3sm 
    workdir=/compyfs/litz372/e3sm_scratch/compare_model_performance 
    plotdir=/compyfs/www/litz372/compare_performance
    html_address=https://compy-dtn.pnl.gov/litz372/compare_performance  
    source /etc/profile.d/modules.sh
    module load python/miniconda4.12.0 
    source /share/apps/python/miniconda4.12.0/etc/profile.d/conda.sh
    source ${workdir}/venv/bin/activate

    if [ ! -d $plotdir ]; then
        mkdir -p $plotdir 
    fi

    compset=F2010-EAMxx-MAM4xx   #F2010-SCREAMv1 
    resolution=ne4pg2_oQU480 
    pe=P32
    runtime=Ln5 
    queue=debug
    wallclock_time=00:05:00

    # SMS test run
    case=SMS_$pe_$runtime.$resolution.$compset.${machine}_$compiler

    branch1=master

    datestr=`date +'%Y%m%d_%H%M%S'`
    casename1=master

    code_root1=$workdir/E3SM-$casename1 

    do_fetch_code=true
    do_run_case=true

    # If you only need to tweak the plot, set the plot_str to the date string of the run.
    do_plot=true 
    #plot_str=20250703_030001

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    # Fetch code from GitHub 
    fetch_code $branch1 $code_root1 &
    wait 

    if [ $? != 0 ]; then
        echo "Error fetching code from GitHub"
        exit 1
    fi

    # Create SMS test case and run it 
    run_case $code_root1 $casename1 &
    wait 

    if [ $? != 0 ]; then
        echo "Error compiling or running case"
        exit 1
    fi

    # Grab timing data and do the plotting
    if [ "${do_plot,,}" != "true" ]; then
        echo $'\n----- Skipping plot -----\n'
        return
    fi
    if [ -z "${plot_str+x}" ]; then
        plot_str=$datestr 
    fi

    case_root1=$workdir/$case.${casename1}_${plot_str}  

    python ${workdir}/E3SM_test_scripts/jenkins/mam4xx_compare_model_performance_plot.py \
        --case1 $case_root1 --casename1 $casename1 \
        --outdir $plotdir --html $html_address              

    if [ $? != 0 ]; then
        echo "Error plotting model performance"
        exit 1
    fi

    echo "Model performance comparison complete!"

}

#---------------------
# Function Definitions
#---------------------

fetch_code() {    
    if [ "${do_fetch_code,,}" != "true" ]; then
        echo $'\n----- Skipping fetch_code -----\n'
        return
    fi
    local branch=$1 
    local path=$2 

    echo "Fetching code from $branch branch to $path..."
    if [ -d $path ]; then
        echo "Code directory $path already exists. Removing it..."
        rm -rf $path 
    fi 
    
    mkdir -p $path 
    pushd $path 
    git clone git@github.com:E3SM-Project/E3SM.git .     
    if [ '$branch' != 'master' ]; then
        git checkout $branch
    fi
    git submodule update --init --recursive     
    popd
} 

run_case() {
    if [ "${do_run_case,,}" != "true" ]; then
        echo $'\n----- Skipping create_newcase -----\n'
        return
    fi

    local code_root=$1 
    local casename=$2 

    local interval=60  # seconds to wait between each check 

    path=$workdir/$case.${casename}_${datestr} 

    # create new case and build it 
    echo "Creating case $case.${casename}_${datestr}..."
    $code_root/cime/scripts/create_test $case \
        -t ${casename}_${datestr} -p $project -q $queue --output-root $workdir --no-run #--no-build   

    if [ $? != 0 ]; then
        echo "Error creating case $case"
        exit 1
    fi   

    # submit job and monitor status
    pushd $path 
    ./xmlchange JOB_WALLCLOCK_TIME=$wallclock_time 
    ./case.submit >& log.submit 

    if [ $? != 0 ]; then
        echo "Error submitting job for $case"
        exit 1
    fi

    jobID=`awk -F " " '($1=="Submitted") {print $NF}' log.submit | tail -n 1 `
    
    while true; do 
        sacct --job $jobID > log.job_stat
        jobST=` awk "{if(NR==3) print}" log.job_stat | awk '{printf"%s\n",$6}'`

        if [ "${jobST}" == "COMPLETED" ]; then
            printf "%s Run complete: %-30s jobID: %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$casename" "$jobID"
            break 
        elif [[ ("${jobST}" == "FAILED") || ("${jobST}" == *"CANCELLED"*) || ("${jobST}" == "TIMEOUT") ]]; then
            printf "%s Run failed: %-30s jobID: %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$casename" "$jobID"
            exit 1 
        else
            printf "%s Waiting for case: %-30s to complete...  jobID: %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$casename" "$jobID"
            sleep $interval
        fi
    done 

    popd 
}

# Silent versions of popd and pushd
pushd() {
    command pushd "$@" > /dev/null
}
popd() {
    command popd "$@" > /dev/null
}

# Run the script
main 
