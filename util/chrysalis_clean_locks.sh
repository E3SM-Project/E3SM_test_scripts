
# OpenMPI creates .loc/.lock files which might stay on after aborted file close, force clean them
echo "chrysalis_clean_locks.sh: lock files beforehand"
find /lcrc/group/e3sm/data/ -name "*\.loc*" -exec ls -altr {} \;

echo "chrysalis_clean_locks.sh: removing lock files..."
find /lcrc/group/e3sm/data/ -name "*\.loc*" -exec rm -f {} \;

echo "chrysalis_clean_locks.sh: lock files afterwards"
find /lcrc/group/e3sm/data/ -name "*\.loc*" -exec ls -altr {} \;

echo "chrysalis_clean_locks.sh: done"
