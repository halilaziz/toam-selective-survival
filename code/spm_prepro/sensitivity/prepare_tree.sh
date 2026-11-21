#!/bin/bash
# Sensitivity analysis (qc_records/SENSITIVITY_COREG_PLAN.md): build derivatives/spmMB_coregfix for the given
# participants by COPYING (never moving) the inputs of step 2 for the modelled runs from derivatives/spmMB.
# derivatives/spmMB is only read. usage: bash prepare_tree.sh sub-60601 sub-62162 ...
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../env.sh"
source "$TOAM/code/spm_prepro/env_spm.sh"
OLD=$TOAM/derivatives/spmMB; NEW=$TOAM/derivatives/spmMB_coregfix
for s in "$@"; do
  [ -d "$NEW/$s" ] && { echo "$NEW/$s exists; remove it first if a fresh copy is wanted"; exit 3; }
  for ses in ses-1 ses-2; do
    o=$OLD/$s/preproc/$ses; n=$NEW/$s/preproc/$ses; guard "$n"
    mkdir -p "$n/func" "$n/anat"
    if [ "$ses" = ses-1 ]; then tasks="forgetexp retrieval"; else tasks="forgetexp"; fi
    for t in $tasks; do
      for f in "$o"/func/rasub-*task-${t}_*bold.nii "$o"/func/rasub-*task-${t}_*bold.mat \
               "$o"/func/meanasub-*task-${t}_*bold.nii "$o"/func/rp_asub-*task-${t}_*bold.txt; do
        [ -f "$f" ] || { echo "missing $f"; exit 4; }; cp -p "$f" "$n/func/"
      done
    done
    for f in "$o"/anat/msub-*T1w.nii "$o"/anat/c1sub-*T1w.nii "$o"/anat/c2sub-*T1w.nii "$o"/anat/c3sub-*T1w.nii \
             "$o"/anat/brainMask*T1w.nii "$o"/anat/skullStripped*T1w.nii "$o"/anat/y_sub-*T1w.nii "$o"/anat/iy_sub-*T1w.nii; do
      [ -f "$f" ] || { echo "missing $f"; exit 4; }; cp -p "$f" "$n/anat/"
    done
  done
  echo "$s: $(find "$NEW/$s" -type f | wc -l) files, $(du -sh "$NEW/$s" | cut -f1)"
done
