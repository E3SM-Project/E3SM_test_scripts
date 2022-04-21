
# OpenMPI creates .loc/.lock files which might stay on after aborted file close, force clean them
find /lcrc/group/e3sm/data/ -name "*\.loc*" -exec rm -f {} \;
