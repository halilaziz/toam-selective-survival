#!/bin/bash
# Queue the fMRIPrep robustness array so it starts only after the SPM12 batch (SGE job name $SPM_JOB, default toam_spm)
# has finished. Low priority; at most $TC (default 4) participants at once.
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
N=$(( $(wc -l < $TOAM/raw/ds006266/participants.tsv) - 1 ))
mkdir -p "$TOAM/logs/fmriprep"
qsub -v TOAM -q "${SGE_QUEUE:-all.q}" -o "$TOAM/logs/fmriprep/" -hold_jid ${SPM_JOB:-toam_spm} -p -100 -t 1-$N -tc ${TC:-4} \
  "$TOAM/code/fmriprep/fmriprep_wb.sge"
