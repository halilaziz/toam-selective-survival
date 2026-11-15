#!/bin/bash
# First-level GLM for one participant: MATLAB R2026a + SPM12 r7771 in the matlab-deps container, through ml_exec
# (code/spm_prepro/env_spm.sh), gently (nice 19, ionice idle, one thread). Writes only inside $TOAM.
#   usage: bash code/analysis/matlab/first_level.sh <spec.json> [tag]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../env.sh"
source "$TOAM/code/spm_prepro/env_spm.sh"
SPEC=$(readlink -m "$1"); TAG=${2:-toam_l1_$(basename "$SPEC" .json)}
guard "$SPEC"
LOG=$TOAM/logs/first_level/$TAG.log; mkdir -p "$(dirname "$LOG")"
HERE=$TOAM/code/analysis/matlab
nice -n 19 ionice -c 3 bash -c 'source "$TOAM/code/env.sh"; source "$TOAM/code/spm_prepro/env_spm.sh"; ml_exec "$@"' _ \
  "$TAG" "$LOG" "addpath('$HERE'); run_first_level('$SPEC')"
