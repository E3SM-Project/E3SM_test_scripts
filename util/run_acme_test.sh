

cd $E3SMREPO
rm -f CMakeCache.txt
cd ./cime/scripts/tests/run_e3sm_ctest
cmake .
ctest --timeout 10000 -D Experimental
