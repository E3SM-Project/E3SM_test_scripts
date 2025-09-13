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

    #Name of the test
    testname="SMS_${simulation_length}"
    
    #compset for MAM4xx
    compset_mam4xx="F2010-EAMxx-MAM4xx"

    #compset for EAMxx
    compset_eamxx="F2010-SCREAMv1"
    
    echo "Configuration: "
    echo "Test ${testname} on ${mach} with ${compiler} compiler"
    echo "Resolution ${resolution} and compsets ${compset_mam4xx} and ${compset_eamxx}" 

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------

    check_if_dir_exists $code_root # exit is code doesn't exists

    #cd into the source code directory
    cd $code_root

    #reset code to the latest master
    if $fetch_root; then
      update_e3sm
    fi

    #create directory for tests from today
    date_str="`date +'%m-%d-%Y__%H_%M_%S'`"

    #extract parent directory of the source code
    parent_dir=$(dirname "$code_root")
    temp_dir="${parent_dir}/perf_test/test_${date_str}"
    
    #create a temporary test directory
    create_temp_dir "$temp_dir"

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
  #  wait_for_run_completion $temp_dir/$mam4xx_dir
    mam4xx_pass=$(wait_for_run_completion $temp_dir/$mam4xx_dir)
    if ! $mam4xx_pass; then
      echo "MAM4xx run FAILED. Stopping..."
      exit
    fi
    
    #Grab MAM4xx timing data
    cd $temp_dir/$mam4xx_dir/timing
    mam4xx_throughput=$(grep Throughput e3sm_timing.* | grep -oP '\d+\.\d+')
    echo "EAMxx+MAM4xx Throughput - ${mam4xx_throughput}"
    mam4xx_cost=$(grep "Model Cost" e3sm_timing.* | grep -oP '\d+\.\d+')
    echo "EAMxx+MAM4xx Model Cost - ${mam4xx_cost}"

    #check if the EAMxx test completed
    eamxx_dir=${testname}.${resolution}.${compset_eamxx}.${mach}_${compiler}.master_${date_str}
    eamxx_pass=$(wait_for_run_completion $temp_dir/$eamxx_dir)
    if ! $eamxx_pass; then
      echo "EAMxx run FAILED. Stopping..."
      exit
    fi

    cd $temp_dir/$eamxx_dir/timing

    #Grab EAMxx timing data
    eamxx_throughput=$(grep Throughput e3sm_timing.* | grep -oP '\d+\.\d+')
    echo "EAMxx Throughput - ${eamxx_throughput}"
    eamxx_cost=$(grep "Model Cost" e3sm_timing.* | grep -oP '\d+\.\d+')
    echo "EAMxx Model Cost - ${eamxx_cost}"

    #save data in a csv file
    cd $data_dest
    DATE=$(date +'%Y-%m-%d')
    echo "${DATE},${mam4xx_throughput},${mam4xx_cost}" >> mam4xx_performance_${resolution}.csv
    echo "${DATE},${eamxx_throughput},${eamxx_cost}" >> eamxx_performance_${resolution}.csv
    echo "data saved at $(pwd)"
    cat mam4xx_performance_${resolution}.csv
    cat eamxx_performance_${resolution}.csv

    # do the plotting
    cd ${parent_dir}
    source .venv/bin/activate
    cd E3SM_test_scripts/jenkins
    python3 mam4xx_plot_compare_performance.py -r $resolution -m $mach -e $compset_eamxx -x $compset_mam4xx -d $data_dest -t $simulation_length

    #copy plot to www dir
    cp ${data_dest}/performance_comp_${DATE}_${resolution}_${simulation_length}.png ${share_dest}/performance_comp_${resolution}_${simulation_length}.png
    chmod 775 ${share_dest}/performance_comp_${resolution}_${simulation_length}.png
    echo "visit ${share_url} for the results!"

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
    git fetch origin && git checkout master && git reset --hard origin/master

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
    -p e3sm -t "master_${date_str}" --output-root "${temp_dir}" -m ${mach} &

}

wait_for_run_completion () {
    local case_dir=$1
    local interval=60 # Seconds to wait between checks
    local elapsed=0

    run_pass=true

    echo "Waiting for test run to complete in $case_dir..."
    wait_til_dir_created $case_dir
    cd "$case_dir" || { echo "Failed to enter $case_dir"; return 1; }

    while true; do
        if [ -f "CaseStatus" ]; then
            if grep -q "Timing" CaseStatus; then
                echo "Run complete! Timing info found in CaseStatus."
                break
            elif grep -q "FAIL" TestStatus; then
                echo "Run failed. See log for more."
                cat CaseStatus
                run_pass=false
                break
            fi
        fi
        echo "Still waiting... elapsed: $((elapsed/60)) min"
        sleep "$interval"
        (( elapsed += interval ))
    done
    return $run_pass
}

wait_til_dir_created() {
    local case_dir=$1
    while [ ! -d "$case_dir" ]; do
        echo "Waiting for $case_dir to be created..."
        sleep 10
    done
}

#-----------------------------
# Check command line args
#-----------------------------

#parse command line args
while getopts ":r:c:t:m:p:f:d:s:u:" opt; do
  case $opt in
    r) resolution="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please provide a valid model resolution using -r command line option" >&2
    exit 1
    ;;
    c) compiler="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please set a valid compiler using -c command line option" >&2
    exit 1
    ;;
    t) simulation_length="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please select a valid simulation_length using -t command line option" >&2
    exit 1
    ;;
    m) mach="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please select a valid machine using -m command line option" >&2
    exit 1
    ;;
    p) code_root="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please select a valid path using -p command line option" >&2
    exit 1
    ;;
    f) fetch_root="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please select a valid boolean using -f command line option" >&2
    exit 1
    ;;
    d) data_dest="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please select a valid data destination using -d command line option" >&2
    exit 1
    ;;
    s) share_dest="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please select a valid shared data destination using -s command line option" >&2
    exit 1
    ;;
    u) share_url="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG; please provide a shared data url using -u command line option" >&2
    exit 1
    ;;
  esac

  case $OPTARG in
    -*) echo "Option $opt needs a valid argument"
    exit 1
    ;;
  esac
done

resolution_pattern="^ne[0-9].*$"
if [ -z "${resolution}" ]; then
    echo "resolution is not set, please set it using -r command line option"
    exit 1
elif [[ ! $resolution =~ $resolution_pattern ]];
then
    echo "Please provide a valid resolution as the first command line parameter."
    exit 1
fi

if [ -z "${compiler}" ]; then
    echo "Compiler is not set, please set it using -c command line option"
    exit 1
fi

if [ -z "${simulation_length}" ]; then
    echo "Timestep is not set, please set it using -t command line option"
    exit 1
fi

if [ -z "${mach}" ]; then
    echo "Machine is not set, please set it using -m command line option"
    exit 1
fi

if [ -z "${code_root}" ]; then
    echo "Code root path is not set, please set it using -p command line option"
    exit 1
fi

if [ -z "${fetch_root}" ]; then
    echo "Fetch code boolean is not set, please set it using -f command line option"
    exit 1
fi

if [ -z "${data_dest}" ]; then
    echo "Data destination path is not set, please set it using -d command line option"
    exit 1
fi

if [ -z "${share_dest}" ]; then
    echo "Shared data destination path is not set, please set it using -s command line option"
    exit 1
fi

if [ -z "${share_url}" ]; then
    echo "Shared data url is not set, please set it using -u command line option"
    exit 1
fi



#--------------------------
# Start the script
#--------------------------
main 
