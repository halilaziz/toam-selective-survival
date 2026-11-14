#!/bin/bash
# One-off preparation for the fMRIPrep robustness run (does NOT run fMRIPrep):
# pull the pinned container into TOAM, record its digest, prefetch TemplateFlow templates into TOAM.
# Gentle: nice 19 and at most 4 CPUs (taskset), because mksquashfs would otherwise use every core.
set -uo pipefail
source /analysis/halilaziz/halil/TOAM/code/env.sh
VER=${1:-25.2.7}; mkdir -p $TOAM/containers $TOAM/tmp/apptainer_home $TEMPLATEFLOW_HOME; cd $TOAM/containers
echo "$(date +%F_%T) start; FreeSurfer license readable: $([ -r /misc/opt/freesurfer7.2/license.txt ] && echo yes || echo NO)"
if [ ! -s fmriprep-$VER.sif ]; then
  taskset -c 0-3 nice -n 19 apptainer pull fmriprep-$VER.sif docker://nipreps/fmriprep:$VER || { echo "pull failed"; exit 1; }
fi
dig=$(curl -s "https://hub.docker.com/v2/repositories/nipreps/fmriprep/tags/$VER" | python3 -c "import json,sys;print(json.load(sys.stdin).get('digest',''))")
echo "$(date +%F) fmriprep $VER docker://nipreps/fmriprep:$VER hub_digest=$dig sif_sha256=$(sha256sum fmriprep-$VER.sif | cut -c1-64)" >> MANIFEST.txt
apptainer exec --cleanenv --contain --home $TOAM/tmp/apptainer_home fmriprep-$VER.sif fmriprep --version
APPTAINERENV_TEMPLATEFLOW_HOME=$TEMPLATEFLOW_HOME taskset -c 0-3 nice -n 19 apptainer exec --cleanenv --contain \
  --home $TOAM/tmp/apptainer_home -B $TOAM fmriprep-$VER.sif python -c "
from templateflow import api as tf
for tpl,kw in [('MNI152NLin2009cAsym',{}),('OASIS30ANTs',{}),('MNI152NLin6Asym',{'resolution':2})]:
    tf.get(tpl, **kw)
print('templateflow ok')"
echo "$(date +%F_%T) done"
