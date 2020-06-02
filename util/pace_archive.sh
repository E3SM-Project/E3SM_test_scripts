# Purpose: Automate performance data upload to PACE
# Author: Sarat Sreepathi (sarat@ornl.gov)

# Allow group write permission for any files generated
umask 002 

echo "Begin PACE archiving."

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
find . -size +50M -exec ls -lh {} \; > large-files-removed.txt
# Delete large files
find . -size +50M -exec rm {} \;

wget -O e3sm_perf_archive.perl https://pace.ornl.gov/static/tools/e3sm_perf_archive.perl
curdate=$(date '+%Y_%m_%d')
perl e3sm_perf_archive.perl > e3sm_perf_archive_${CIME_MACHINE}_${curdate}_out.txt
mv e3sm_perf_archive_${CIME_MACHINE}_${curdate}_out.txt performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate}
./pace-upload --perf-archive ./performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate}

# Find handles the case gracefully when no pace*log is generated when no completed experiments were found
find . -iname "pace-*.log" -type f -exec mv {} performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate} \;
mv large-files-removed.txt performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate}

# No need to tar at this point - will enable when we store to HPSS
# tar zcf performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate}.tar.gz performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate}

# Move processed exps into old perf data archive
curmonth=$(date '+%Y-%m')
mkdir -p ${OLD_PERF_ARCHIVE_DIR}/${curmonth}
mv performance_archive_${CIME_MACHINE}_${PROJ_SPACE_TAG}_${curdate}* ${OLD_PERF_ARCHIVE_DIR}/${curmonth}

echo "Completed PACE archiving."
