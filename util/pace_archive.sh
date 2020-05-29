# Purpose: Automate performance data upload to PACE
# Author: Sarat Sreepathi (sarat@ornl.gov)

# The performance archive directory on the platform is the working dir
cd ${PERF_ARCHIVE_DIR}

# Download PACE upload script
if [[ -z "${PACE_PYTHON3}" ]] ; then
	# Python2 version (supported by system Python without requiring module load)
	echo "PACE Python 2"
	wget -O pace-upload https://pace.ornl.gov/static/tools/pace-upload
else
	# Python3 version (requires Anaconda/Python module with requests package)
	echo "PACE Python 3"
	wget -O pace-upload https://pace.ornl.gov/static/tools/pace-upload3
fi

chmod +x pace-upload

# Performance archive should not contain large files (empirical threshold of 50MB)
# List any large files 
echo "Large file list:"
find . -size +50M -exec ls -lh {} \;
# Delete large files
find . -size +50M -exec rm {} \;

curdate=$(date '+%Y_%m_%d')
perl e3sm_perf_archive.perl > e3sm_perf_archive_${CIME_MACHINE}_${curdate}_out.txt
mv e3sm_perf_archive_${CIME_MACHINE}_${curdate}_out.txt performance_archive_${CIME_MACHINE}_all_${curdate}
./pace-upload --perf-archive ./performance_archive_${CIME_MACHINE}_all_${curdate}
if [ $? -ne 0 ]
then
  echo "Error: pace-upload failed. Check log."
  exit 4
fi 
mv pace-*.log performance_archive_${CIME_MACHINE}_all_${curdate}
tar zcf performance_archive_${CIME_MACHINE}_all_${curdate}.tar.gz performance_archive_${CIME_MACHINE}_all_${curdate}

# Move processed exps into old perf data archive
curmonth=$(date '+%Y-%m')
mkdir -p ${OLD_PERF_ARCHIVE_DIR}/${curmonth}
mv performance_archive_${CIME_MACHINE}_all_${curdate}* ${OLD_PERF_ARCHIVE_DIR}/${curmonth}

