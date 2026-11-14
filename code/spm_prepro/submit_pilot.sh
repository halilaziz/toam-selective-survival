#!/bin/bash
# Submit the two SPM pilot jobs: the first participant of each participants.tsv (ds006265 small-FOV, ds006266 whole-brain).
# Checks the queue first; refuses if toam_spm jobs are already queued or running.
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
source "$(dirname "${BASH_SOURCE[0]}")/env_spm.sh"
mkdir -p "$TOAM/logs/spm"
Q=${SGE_QUEUE:-all.q}
echo "== $Q before submitting ($(date '+%F %T %Z')):"; qstat -u '*' -q "$Q"; qstat -f -q "$Q" | sed -n 3p
mine=$(qstat -u "$(id -un)" | awk 'NR>2 && $3=="toam_spm"' | wc -l)
[ "$mine" -eq 0 ] || { echo "toam_spm jobs already queued/running: $mine; not submitting"; exit 1; }
for ds in ds006265 ds006266; do
  sub=$(sed -n 2p "$TOAM/raw/$ds/participants.tsv" | cut -f1)
  qsub -N toam_spm -v TOAM -q "$Q" -pe smp 1 -p -100 -wd "$TOAM/logs/spm" -o "$TOAM/logs/spm/" -e "$TOAM/logs/spm/" \
       "$SPMP/toam_spm.sge" "$sub"
done
qstat -u "$(id -un)" | awk 'NR<=2 || $3=="toam_spm"'
