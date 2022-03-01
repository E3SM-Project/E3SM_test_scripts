
# .nc files producted by E3SM on blues/anvil seem to be locked-down, regardless of umask
# so we must force the issue here.
chmod -R g+rwX /lcrc/group/e3sm/$USER/scratch
