
cd $SCRIPTROOT/..

cd E3SM/cime
git reset --hard origin/master
cd -

/bin/rm -rf build
mkdir build
cd build
cmake ../E3SM/cime/scripts/tests
ctest -D NightlyStart -D NightlyTest -D NightlySubmit
