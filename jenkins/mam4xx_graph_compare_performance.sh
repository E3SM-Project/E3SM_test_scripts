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

    #set levels test modifier
    test_mod="eamxx-L72"
    
    echo "Configuration: "
    echo "Test ${testname} on ${mach} with ${compiler} compiler and ${test_mod} modifier"
    echo "Resolution ${resolution} and compsets ${compset_mam4xx} and ${compset_eamxx}" 

    #---------------------------------------------------------------
    # User-defined configuration ENDs
    #---------------------------------------------------------------



    #create directory for tests from today
    date_str="`date +'%m-%d-%Y'`"

    #extract parent directory of the source code
    parent_dir=$(dirname "$code_root")


    # --- Configuration ---
    eamxx_csv=${data_dest}/eamxx_performance_${resolution}.csv
    mam4xx_csv=${data_dest}/mam4xx_performance_${resolution}.csv
    data_dir="${parent_dir}/perf_test"

    echo "Checking for new data..."
    echo "------------------------------------------------"

    # 1. Loop through the directories in the data folder
    # We use find to get only directories and avoid issues with spaces/wildcards
    find "$data_dir" -maxdepth 1 -type d -name "test_*" | while read -r dir_path; do
    
        # Get just the folder name (e.g., test_10-27-2026__00_24_12)
        dir_name=$(basename "$dir_path")

        # 2. Extract the date part (the second field when splitting by underscore)
        # Result: 10-27-2026
        raw_date=$(echo "$dir_name" | cut -d'_' -f2)
	timestamp=$(echo "$dir_name" | cut -c 16-)

        # 3. Reformat MM-DD-YYYY to YYYY-MM-DD to match the CSV
        # We split by '-' and rearrange the fields
        formatted_date=$(echo "$raw_date" | awk -F'-' '{print $3"-"$1"-"$2}')

        # 4. Check if this formatted date exists as the first column in the CSV
        # grep -q returns 0 (true) if found, 1 (false) if not
        if ! grep -q "^${formatted_date}," "$eamxx_csv"; then
       	    echo "NEW DATE FOUND: $dir_name (Date: $formatted_date)"
            mam4xx_dir=${testname}.${resolution}.${compset_mam4xx}.${mach}_${compiler}.${test_mod}.master_${date_str}${timestamp}
            eamxx_dir=${testname}.${resolution}.${compset_eamxx}.${mach}_${compiler}.${test_mod}.master_${date_str}${timestamp}
	    check_for_run_completion $parent_dir/perf_test/$dir_name/$mam4xx_dir
	    check_for_run_completion $parent_dir/perf_test/$dir_name/$eamxx_dir

	    scrape_data "$parent_dir/perf_test/$dir_name" $mam4xx_dir $eamxx_dir $data_dest $resolution
        fi
    done

    echo "------------------------------------------------"
    echo "Check complete."


    # do the plotting
    if [ "$mach" = "pm-gpu" ]; then
      source /global/cfs/projectdirs/e3sm/litzingj/.venv/bin/activate
    elif [ "$mach" = "compy" ]; then
      source ${parent_dir}/.venv/bin/activate
    fi
    cd ${parent_dir}/E3SM_test_scripts/jenkins
    python3 mam4xx_plot_compare_performance.py -r $resolution -m $mach -e $compset_eamxx -x $compset_mam4xx -d $data_dest -t $simulation_length

    #copy plot to www dir
    DATE=$(date +'%Y-%m-%d')
    cp ${data_dest}/performance_comp_${DATE}_${resolution}_${simulation_length}.png ${share_dest}/performance_comp_${resolution}_${simulation_length}.png
    chmod 775 ${share_dest}/performance_comp_${resolution}_${simulation_length}.png
    echo "visit ${share_url} for the results!"

}


#---------------------
# Function Definitions
#---------------------

#scrape data from timing file
scrape_data() {
    dir_name=$1
    mam4xx_dir=$2
    eamxx_dir=$3
    data_dest=$4
    resolution=$5

    #Grab MAM4xx timing data
    cd $dir_name/$mam4xx_dir/timing
    mam4xx_throughput=$(grep Throughput e3sm_timing.* | grep -oP '\d+\.\d+')
    echo "EAMxx+MAM4xx Throughput - ${mam4xx_throughput}"
    mam4xx_cost=$(grep "Model Cost" e3sm_timing.* | grep -oP '\d+\.\d+')
    echo "EAMxx+MAM4xx Model Cost - ${mam4xx_cost}"
                                                                            
    #Grab EAMxx timing data
    cd $dir_name/$eamxx_dir/timing
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

    return 0
}

#check if the directory exists otherwise exit
check_if_dir_exists () {
    if [ ! -d "$1" ]; then
        echo "$1 directory doesnt exists. Please ensure directory is there to procced"
        exit 1
    fi
}

check_for_run_completion () {
    local case_dir=$1

    echo "Checking if test run complete in $case_dir..."
    check_if_dir_exists $case_dir
    cd "$case_dir" || { echo "Failed to enter $case_dir"; return 1; }
    check_if_dir_exists "timing"
    echo "Timing dir exists, can proceed with collecting timing data"

    return 0 
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
    f) hard_reset_E3SM="$OPTARG"
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

if [ -z "${hard_reset_E3SM}" ]; then
    echo "Boolean for fetching latest E3SM is not set, please set it using -f command line option"
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
