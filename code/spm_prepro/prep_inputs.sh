#!/bin/bash
# Copy (gunzip) one participant's BIDS T1w and BOLD images into the layout the authors' SPM code reads:
#   $TOAM/derivatives/spmMB/sub-<id>/preproc/ses-<n>/{anat,func}/<BIDS file name without .gz>
# This replaces the authors' utilities/gunziploopHIPP.m, which fmri/preprocessing/prepro.sh (line 37, commented
# out) called but which is not in their repository. File names stay the BIDS names (their scripts select
# '^sub.*<task>.*\.nii$' and '^sub.*T1w.nii$'; their plotting code shows e.g.
# spmMB/sub-60601/preproc/ses-1/anat/wskullStrippedsub-60601_ses-1_acq-t1csmp2ragesag06mmUNIDEN_T1w.nii).
# SPM writes prefixed outputs next to its inputs, so the inputs are copies; raw/ is only read.
# usage: prep_inputs.sh sub-60601
set -euo pipefail
source /analysis/halilaziz/halil/TOAM/code/env.sh
source /analysis/halilaziz/halil/TOAM/code/spm_prepro/env_spm.sh
SUB=$1
DS=$(arm_of "$SUB"); [ -n "$DS" ] || { echo "unknown participant $SUB" >&2; exit 2; }
shopt -s nullglob
n=0; made=()
for ses in ses-1 ses-2; do
  for mod in anat func; do
    out=$DERIV/$SUB/preproc/$ses/$mod; guard "$out"; mkdir -p "$out"
    case $mod in
      anat) srcs=("$TOAM/raw/$DS/$SUB/$ses/anat/${SUB}_${ses}_"*_T1w.nii*) ;;
      func) srcs=("$TOAM/raw/$DS/$SUB/$ses/func/${SUB}_${ses}_task-"*_bold.nii*) ;;
    esac
    for src in "${srcs[@]}"; do
      dst=$out/$(basename "$src" .gz)
      if [[ "$src" == *.gz ]]; then gzip -dc "$src" > "$dst.part"; else cp "$src" "$dst.part"; fi  # cp follows the annex symlink
      mv "$dst.part" "$dst"; n=$((n+1)); made+=("$dst")
      echo "$(date '+%T') $src -> $dst ($(stat -c %s "$dst") bytes)"
    done
  done
done
[ "$n" -eq 6 ] || { echo "expected 6 images (2 T1w + 4 BOLD), got $n" >&2; exit 3; }
# each copy must be complete: file size = vox_offset + voxels x bytes per voxel (from its NIfTI-1 header)
python3 -I - "${made[@]}" <<'PY'
import struct, sys, os
bad = 0
for f in sys.argv[1:]:
    h = open(f, 'rb').read(348)
    dim = struct.unpack('<8h', h[40:56]); bitpix = struct.unpack('<h', h[72:74])[0]; off = struct.unpack('<f', h[108:112])[0]
    n = 1
    for d in dim[1:dim[0] + 1]: n *= d
    exp = int(off) + n * bitpix // 8; got = os.path.getsize(f)
    print(f"{os.path.basename(f)} dim={dim[1:dim[0]+1]} bitpix={bitpix} expected={exp} size={got} {'OK' if exp == got else 'MISMATCH'}")
    bad += exp != got
sys.exit(1 if bad else 0)
PY
