#!/bin/bash -xle
# Purpose: Automate performance data upload to PACE
# Author: Sarat Sreepathi (sarat@ornl.gov)

# boiler: every script must have these three lines
export SCRIPTROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export CIME_MACHINE=compy
source $SCRIPTROOT/util/setup_common.sh

# Performance archive directory on this platform
PERF_ARCHIVE_DIR=/compyfs/performance_archive
# Archives of old performance data on this platform
OLD_PERF_ARCHIVE_DIR=/compyfs/OLD_PERF

# The performance archive directory on the platform is the working dir
cd ${PERF_ARCHIVE_DIR}

if [ $? -ne 0 ]
then
  echo "Error:Unable to change working directory to ${PERF_ARCHIVE_DIR}"
  exit 1
fi 

# Download PACE upload script
# Python2 version (supported by system Python without requiring module load)
wget -O pace-upload https://pace.ornl.gov/static/tools/pace-upload
# Python3 version (requires Anaconda/Python module with requests package)
#wget -O pace-upload https://pace.ornl.gov/static/tools/pace-upload3

if [ $? -ne 0 ]
then
  echo "Error: Unable to download pace-upload script."
  exit 2
fi 

chmod +x pace-upload

# Performance archive should not contain large files (empirical threshold of 50MB)
# List any large files 
echo "Large file list:"
find . -size +50M -exec ls -lh {} \;
# Delete large files
find . -size +50M -exec rm {} \;
if [ $? -ne 0 ]
then
  echo "Error: Unable to delete large files before preparing upload package."
  exit 3
fi 

curdate=$(date '+%Y_%m_%d')
perl e3sm_perf_archive.perl > e3sm_perf_archive_compy_${curdate}_out.txt
mv e3sm_perf_archive_compy_${curdate}_out.txt performance_archive_compy_all_${curdate}
./pace-upload --perf-archive ./performance_archive_compy_all_${curdate}
if [ $? -ne 0 ]
then
  echo "Error: pace-upload failed. Check log."
  exit 4
fi 
mv pace-*.log performance_archive_compy_all_${curdate}
tar zcf performance_archive_compy_all_${curdate}.tar.gz performance_archive_compy_all_${curdate}

# Move processed exps into old perf data archive
curmonth=$(date '+%Y-%m')
mkdir -p ${OLD_PERF_ARCHIVE_DIR}/${curmonth}
mv performance_archive_compy_all_${curdate}* ${OLD_PERF_ARCHIVE_DIR}/${curmonth}

