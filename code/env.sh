# Workspace settings for the TOAM re-analysis; every script sources this file first.
# All writes stay inside the workspace root $TOAM: HOME, TMPDIR and every cache are redirected into it.
# $TOAM defaults to the folder that contains code/. Site settings (SGE queue, MATLAB binary and licence,
# FreeSurfer licence) go in code/site.local.sh, which is not tracked: copy code/site.example.sh and edit it.
_toam_code=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[ -f "$_toam_code/site.local.sh" ] && source "$_toam_code/site.local.sh"
export TOAM=${TOAM:-$(dirname "$_toam_code")}
unset _toam_code
export HOME=$TOAM/tmp/home TMPDIR=$TOAM/tmp/tmp
export XDG_CACHE_HOME=$TOAM/tmp/cache XDG_CONFIG_HOME=$TOAM/tmp/config XDG_DATA_HOME=$TOAM/tmp/share
export PIP_CACHE_DIR=$TOAM/tmp/cache/pip MPLCONFIGDIR=$TOAM/tmp/cache/mpl PYTHONNOUSERSITE=1
export APPTAINER_CACHEDIR=$TOAM/tmp/cache/apptainer APPTAINER_TMPDIR=$TOAM/tmp/apptainer
export TEMPLATEFLOW_HOME=$TOAM/tmp/templateflow NILEARN_DATA=$TOAM/tmp/nilearn_data
export GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
mkdir -p "$HOME" "$TMPDIR" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
umask 002
