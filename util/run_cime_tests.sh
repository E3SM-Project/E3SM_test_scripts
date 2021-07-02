
cd $SCRIPTROOT/..

cd E3SM/cime
# This is a subtle issue. Jenkins/Git will not fetch submodules
# that are already up-to-date, so origin may not have recent CIME
# changes. We need to fetch here and use https since we can't be
# certain of the ssh key situation.
git fetch https://github.com/ESMCI/cime.git
git reset --hard FETCH_HEAD
cd -

/bin/rm -rf build
mkdir build
cd build
cmake ../E3SM/cime/scripts/tests
ctest -D NightlyStart -D NightlyTest -D NightlySubmit
