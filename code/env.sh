# TOAM workspace on milner. Golden rule (Halil 2026-11-12): write, change or delete ONLY inside $TOAM.
export TOAM=/analysis/halilaziz/halil/TOAM
export HOME=$TOAM/tmp/home TMPDIR=$TOAM/tmp/tmp
export XDG_CACHE_HOME=$TOAM/tmp/cache XDG_CONFIG_HOME=$TOAM/tmp/config XDG_DATA_HOME=$TOAM/tmp/share
export PIP_CACHE_DIR=$TOAM/tmp/cache/pip MPLCONFIGDIR=$TOAM/tmp/cache/mpl PYTHONNOUSERSITE=1
export APPTAINER_CACHEDIR=$TOAM/tmp/cache/apptainer APPTAINER_TMPDIR=$TOAM/tmp/apptainer
export TEMPLATEFLOW_HOME=$TOAM/tmp/templateflow NILEARN_DATA=$TOAM/tmp/nilearn_data
export GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
mkdir -p "$HOME" "$TMPDIR" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
umask 002
