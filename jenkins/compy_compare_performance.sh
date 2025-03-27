#!/bin/bash

#This script runs 2 simulations:
# 1. Current master with MAM4xx
# 2. Current master default EAMxx


update_git () {
    echo "Updating the E3SM repo..."
    git fetch --all
    git pull origin master
    git submodule deinit -f . && git submodule update --init --recursive
    git submodule update --init --recursive
    git submodule sync --recursive
}

main() {

    source /etc/profile.d/modules.sh

    #path to E3SM
    code_root="/compyfs/litz372/e3sm_scratch/performance_testing/E3SM"
    

    #machine to run the test on
    mach="compy"
    mach_compiler="${mach}_intel"
    
    if [ $mach == "compy" ]; then
        module load cmake/3.19.6 gcc/8.1.0  mvapich2/2.3.1 python/3.7.3
    fi

    #Resolution
    resolution="ne4pg2_ne4pg2"
    compset="F2010-SCREAMv1"
    
    cd $code_root
    update_git

    #create directory for tests from today
    date_str="`date +'%m-%d-%Y__%H_%M_%S'`"
    temp_dir="../test_${date_str}"
    echo "creating $temp_dir for this test..."
    mkdir -p ${temp_dir}
    echo "test dir is ${temp_dir}..."

    #run 1 (Current master with MAM4xx)
    cd cime/scripts

    mam4xx_testname=SMS_Ln5.${resolution}.${compset}.${mach_compiler}.eamxx-mam4xx-all_mam4xx_procs
    eamxx_testname=SMS_Ln5.${resolution}.${compset}

    echo "starting EAMxx+MAM4xx test..."
    ./create_test ${mam4xx_testname}  -p e3sm -t "master_${date_str}" --output-root "../../${temp_dir}" &

    #run 2 (Current master default EAMxx)
    echo "starting EAMxx default test..."
    ./create_test ${eamxx_testname} --compiler intel  -p e3sm -t "master_${date_str}" --output-root "../../${temp_dir}" & # --wait

    mam4xx_dir=${mam4xx_testname}.master_${date_str}
    eamxx_dir=${eamxx_testname}.${mach_compiler}.master_${date_str}

    sleep 120
    
    #figure out when these runs are done (option: a while loop to check status sleeping for 30 seconds)
    cd ${code_root}/${temp_dir}
    cd ${mam4xx_dir}

    #wait for EAMxx+MAM4xx test to finish 
    mam4xx_done=""
    while [[ -z $mam4xx_done ]]
    do
        sleep 60
        echo "checking if MAM4xx Timing file has been created... "
        grep Timing CaseStatus
        mam4xx_done=$(grep Timing CaseStatus)
    done

    #extract EAMxx+MAM4xx timing
    cd timing
    mam4xx_throughput=$(grep Throughput e3sm_timing.${mam4xx_testname}*)
    mam4xx_throughput=$(echo ${mam4xx_throughput} | grep -oP '\d+\.\d+')
    echo "EAMxx+MAM4xx Throughput - ${mam4xx_throughput}"

    #wait for EAMxx default test to finish 
    cd ../../${eamxx_dir}
    eamxx_done=""
    while [[ -z $eamxx_done ]]
    do
        sleep 60
        echo "checking if EAMxx Timing file has been created... "
        grep Timing CaseStatus
        eamxx_done=$(grep Timing CaseStatus)
    done

    #extract EAMxx+default timing
    cd timing
    eamxx_throughput=$(grep Throughput e3sm_timing.${eamxx_testname}*)
    eamxx_throughput=$(echo ${eamxx_throughput} | grep -oP '\d+\.\d+')
    echo "EAMxx default Throughput - ${eamxx_throughput}"

    #save data in a csv file
    cd /qfs/projects/eagles/litz372/performance_data
    DATE=$(date +'%Y-%m-%d')
    echo "${DATE},${mam4xx_throughput}" >> mam4xx_performance_${resolution}.csv
    echo "${DATE},${eamxx_throughput}" >> eamxx_performance_${resolution}.csv
    echo "data saved at $(pwd)"
    cat mam4xx_performance_${resolution}.csv
    cat eamxx_performance_${resolution}.csv

    # do the plotting
    cd ${code_root}/../
    source .venv/bin/activate
    cd E3SM_test_scripts/jenkins
    python3 compy_plot_compare_performance.py $resolution

   #copy plot to /compyfs/www
   cp /qfs/projects/eagles/litz372/performance_data/performance_comp_${DATE}_${resolution}.png /compyfs/www/litz372/performance_data/performance_comp_${resolution}.png
   echo "visit https://compy-dtn.pnl.gov/litz372/performance_data/performance_comp_${resolution}.png for the results!"
}

main