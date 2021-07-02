
cd $SCRIPTROOT/..

cd E3SM/cime
# This is a subtle issue. Jenkins/Git will not fetch submodules
# that are already up-to-date, so origin may not have recent CIME
# changes. We need to fetch here and use https since we can't be
# certain of the ssh key situation.
git remote set-url origin https://github.com/ESMCI/cime.git
git remote -v
git fetch origin
git reset --hard origin/master
cd -

/bin/rm -rf build
mkdir build
cd build
cmake ../E3SM/cime/scripts/tests
ctest -D NightlyStart -D NightlyTest -D NightlySubmit
