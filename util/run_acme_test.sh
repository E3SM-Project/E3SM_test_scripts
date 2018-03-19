

cd $E3SMREPO
rm -f CMakeCache.txt
cd ./cime/scripts/tests/run_e3sm_ctest
cmake -D SITE="${CIME_MACHINE}" .
ctest --timeout 10000 -D Experimental
