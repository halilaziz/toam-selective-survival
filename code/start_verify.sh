#!/bin/bash
# Independent SHA-256 audit of all 266 annexed files (aria2c already checked each at download). Gentle: nice 19 + ionice idle.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd $TOAM; ts=$(date +%Y%m%d_%H%M)
setsid nohup nice -n 19 ionice -c 3 python3 $TOAM/code/verify.py > logs/verify_$ts.out 2>&1 < /dev/null &
echo $! > logs/verify.pid; echo "verify started, pid $(cat logs/verify.pid), log logs/verify_$ts.out"
