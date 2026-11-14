#!/bin/bash
# Gentle, resumable download: nice 19 + ionice idle, 6 files x 4 connections, capped at 50 MiB/s overall.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd $TOAM; ts=$(date +%Y%m%d_%H%M)
setsid nohup nice -n 19 ionice -c 3 aria2c --no-conf -i manifests/aria2_input.txt -j 6 -x 4 -s 4 --min-split-size=64M \
  --max-overall-download-limit=50M --file-allocation=none --continue=true --check-integrity=true \
  --max-tries=20 --retry-wait=30 --auto-file-renaming=false --summary-interval=300 --console-log-level=warn \
  --save-session=manifests/aria2_session.txt --log=logs/aria2_$ts.log --log-level=notice \
  > logs/aria2_console_$ts.out 2>&1 < /dev/null &
echo $! > logs/aria2.pid; echo "aria2c started, pid $(cat logs/aria2.pid), log logs/aria2_$ts.log"
