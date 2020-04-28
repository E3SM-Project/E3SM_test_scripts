
cd $SCRIPTROOT/..

/bin/rm -rf E3SM/cime
mv cime E3SM/cime

/bin/rm -rf build
mkdir build
cd build
cmake ../E3SM/cime/scripts/tests
ctest -D NightlyStart -D NightlyTest -D NightlySubmit
