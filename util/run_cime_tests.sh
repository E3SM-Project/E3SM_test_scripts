
cd $SCRIPTROOT/..
/bin/rm -rf build
mkdir build
cd build
cmake ../cime/scripts/tests
ctest -D NightlyStart -D NightlyTest -D NightlySubmit
