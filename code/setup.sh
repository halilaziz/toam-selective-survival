#!/bin/bash
# Clone the two TOAM datasets at tag 1.0.2 (metadata, events, sidecars; imaging stays as git-annex symlinks)
# and build the download manifest. Everything is written inside $TOAM.
set -euo pipefail
source /analysis/halilaziz/halil/TOAM/code/env.sh
mkdir -p $TOAM/raw $TOAM/logs $TOAM/manifests
cd $TOAM/raw
for ds in ds006265 ds006266; do
  if [ ! -d $ds/.git ]; then git -c advice.detachedHead=false clone -q --depth 1 --branch 1.0.2 https://github.com/OpenNeuroDatasets/$ds.git $ds; fi
  # NFS shows every file as owned by 'nobody', so git's ownership check is bypassed per command (no config is written)
  echo "$ds: tag $(git -c safe.directory='*' -C $ds describe --tags) | commit $(git -c safe.directory='*' -C $ds rev-parse --short HEAD) | files in git: $(git -c safe.directory='*' -C $ds ls-files | wc -l)"
done
python3 $TOAM/code/make_aria2_input.py
