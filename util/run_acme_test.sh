

cd ${SCRIPTROOT}/util/run_e3sm_ctest
rm -f CMakeCache.txt
cmake .
ctest --timeout 10000 -D Experimental
