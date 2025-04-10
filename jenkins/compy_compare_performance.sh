#!/bin/bash

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Description:
#   This script automates the process of running two E3SM tests:
#     1. EAMxx with MAM4xx (MAM4xx compset)
#     2. EAMxx default (standard SCREAMv1 compset)
#
#   It does the following:
#     - Verifies that the E3SM source directory exists
#     - Resets the repo to the latest master and updates submodules
#     - Creates a timestamped temporary test directory
#     - Builds and runs both tests under the same configuration
#
# Usage:
#   Customize the user input section below before running the script.
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

main() {

    #---------------------------------------------------------------
    # User-defined configuration
    #---------------------------------------------------------------
    #path to E3SM
    code_root="/compyfs/litz372/e3sm_scratch/performance_testing/E3SM"

    #Name of the test
    testname="SMS_Ln5"
    
    #machine to run the test on
    mach="compy"

    #compiler to use
    compiler="intel"

    #Resolution
    resolution="ne4pg2_ne4pg2"

    #compset for MAM4xx
    compset_mam4xx="F2010-EAMxx-MAM4xx"

    #compset for EAMxx
    compset_eamxx="F2010-SCREAMv1"
    
    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    check_if_dir_exists $code_root # exit is code doesn't exists

    #cd into the source code directory
    cd $code_root

    #reset code to the latest master
    update_e3sm

    #create directory for tests from today
    date_str="`date +'%m-%d-%Y__%H_%M_%S'`"

    #extract parent directory of the source code
    parent_dir=$(dirname "$code_root")
    temp_dir="${parent_dir}/test_${date_str}"
    
    #create a temporary test directory
    create_temp_dir "$temp_dir"

    #source the modules so that other modules are available to load
    source /etc/profile.d/modules.sh
    module load python/3.11.5

    #cd into cime/scripts
    check_if_dir_exists cime/scripts # exit is code doesn't exists
    cd cime/scripts

    #Run E3SM tests
    echo "starting EAMxx+MAM4xx test..."
    run_e3sm_test $resolution $compset_mam4xx $mach $compiler $testname $temp_dir

    echo "starting EAMxx default test..."
    run_e3sm_test $resolution $compset_eamxx $mach $compiler $testname $temp_dir

    #wait for the tests directories to be created
    sleep 120

    #check if the EAMxx+MAM4xx test completed
    mam4xx_dir=${testname}.${resolution}.${compset_mam4xx}.${mach}_${compiler}.master_${date_str}
    wait_for_run_completion $temp_dir/$mam4xx_dir
    
    #Grab MAM4xx timing data
    cd $temp_dir/$mam4xx_dir/timing
    mam4xx_throughput=$(grep Throughput e3sm_timing.*)
    mam4xx_throughput=$(echo ${mam4xx_throughput} | grep -oP '\d+\.\d+')
    echo "EAMxx+MAM4xx Throughput - ${mam4xx_throughput}"

    #check if the EAMxx test completed
    eamxx_dir=${testname}.${resolution}.${compset_eamxx}.${mach}_${compiler}.master_${date_str}
    wait_for_run_completion $temp_dir/$eamxx_dir
    cd $temp_dir/$eamxx_dir/timing

    #Grab EAMxx timing data
    eamxx_throughput=$(grep Throughput e3sm_timing.*)
    eam4xx_throughput=$(echo ${eamxx_throughput} | grep -oP '\d+\.\d+')
    echo "EAMxx Throughput - ${eamxx_throughput}"


    #save data in a csv file
    cd /qfs/projects/eagles/litz372/performance_data
    DATE=$(date +'%Y-%m-%d')
    echo "${DATE},${mam4xx_throughput}" >> mam4xx_performance_${resolution}.csv
    echo "${DATE},${eamxx_throughput}" >> eamxx_performance_${resolution}.csv
    echo "data saved at $(pwd)"
    cat mam4xx_performance_${resolution}.csv
    cat eamxx_performance_${resolution}.csv

    # do the plotting
    cd ${parent_dir}
    source .venv/bin/activate
    cd E3SM_test_scripts/jenkins
    python3 compy_plot_compare_performance.py $resolution

   #copy plot to /compyfs/www
   cp /qfs/projects/eagles/litz372/performance_data/performance_comp_${DATE}_${resolution}.png /compyfs/www/litz372/performance_data/performance_comp_${resolution}.png
   echo "visit https://compy-dtn.pnl.gov/litz372/performance_data/performance_comp_${resolution}.png for the results!"
}


#---------------------
# Function Definitions
#---------------------

#check if the directory exists otherwise exit
check_if_dir_exists () {
    if [ ! -d "$1" ]; then
        echo "$1 directory doesnt exists. Please ensure directory is there to procced"
        exit 1
    fi
}

#Update the E3SM repo by hard reseting to the latest master
update_e3sm () {
    echo "Updating the E3SM repo..."
    echo "  Reset code to the latest master ..."
    git fetch origin && git co master && git reset --hard origin/master

    echo "  Update submodules..."
    git submodule deinit -f . && git submodule update --init --recursive
}

# Create a temporary test output directory
create_temp_dir() {
    local dir="$1"
    echo "Creating test directory: $dir"
    mkdir -p "$dir"
    echo "Test directory created."
}

# Build and run a test with given configuration
run_e3sm_test () {
    # receive the parameters
    local resolution=$1
    local compset=$2
    local mach=$3
    local compiler=$4
    local testname=$5
    local temp_dir=$6

    #launch tests
    echo "Launching Test:"
    echo "Creating test: ${testname}.${resolution}.${compset}"
    ./create_test ${testname}.${resolution}.${compset} --compiler $compiler  \
    -p e3sm -t "master_${date_str}" --output-root "${temp_dir}" &

}

wait_for_run_completion () {
    local case_dir=$1
    local interval=60 # Seconds to wait between checks
    local elapsed=0

    echo "Waiting for test run to complete in $case_dir..."
    wait_till_dir_created $case_dir
    cd "$case_dir" || { echo "Failed to enter $case_dir"; return 1; }

    while true; do
        if [ -f "CaseStatus" ]; then
            if grep -q "Timing" CaseStatus; then
                echo "Run complete! Timing info found in CaseStatus."
                break
            fi
        fi
        echo "Still waiting... elapsed: $((elapsed/60)) min"
        sleep "$interval"
        (( elapsed += interval ))
    done
}

wait_till_dir_created() {
    local case_dir=$1
    while [ ! -d "$case_dir" ]; do
        echo "Waiting for $case_dir to be created..."
        sleep 10
    done
}

#--------------------------
# Start the script
#--------------------------
main