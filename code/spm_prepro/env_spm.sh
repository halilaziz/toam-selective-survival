# SPM12 preprocessing of TOAM (adaptation of the authors' SPM code): shared settings.
# Source AFTER /analysis/halilaziz/halil/TOAM/code/env.sh.
# Golden rule (Halil 2026-11-12): create, change or delete ONLY inside $TOAM. raw/ is read-only.
: "${TOAM:?source code/env.sh first}"
export SPMP=$TOAM/code/spm_prepro
export SPM12=$TOAM/tools/spm12                                  # SPM12 r7771 (github.com/spm/spm12, tag r7771)
export MLIMG=$TOAM/tools/containers/matlab-deps_r2026a.sif     # mathworks/matlab-deps:r2026a (Ubuntu 24.04, glibc 2.39)
export MLBIN=/misc/opt/matlab2026a/bin/matlab                  # the binary /misc/bin/matlab -> matlab2026a runs
export MLLIC=/misc/matlab/SITE_LICENCE.lic                    # site licence file passed with -c (file name redacted in the public history)
export DERIV=$TOAM/derivatives/spmMB QCDIR=$TOAM/derivatives/spmMB_qc
export TMP=$TMPDIR TEMP=$TMPDIR

in_toam() { case "$(readlink -m "$1")" in "$TOAM"/*) return 0 ;; *) return 1 ;; esac; }
guard() { local p; for p in "$@"; do in_toam "$p" || { echo "GUARD: refusing to write outside TOAM: $p" >&2; exit 90; }; done; }
arm_of() {  # sub-XXXXX -> ds006265 (small-FOV, 'hipp') or ds006266 (whole-brain, 'wb')
  if grep -q -P "^$1\t" "$TOAM/raw/ds006265/participants.tsv"; then echo ds006265
  elif grep -q -P "^$1\t" "$TOAM/raw/ds006266/participants.tsv"; then echo ds006266; fi; }

# MATLAB R2026a runs inside the matlab-deps container: on milner's openSUSE Tumbleweed (glibc 2.44) the host
# MATLAB segfaults in FlexLM lc_new_job during the licence checkout (tested 2026-11-12; same on hebb 2026-10-27).
# --contain + --workdir: the container's /tmp and /var/tmp live in $TOAM/tmp/apptainer/<tag>; /dev/shm is a private tmpfs.
# --pid: every process MATLAB starts (Xvfb, service host) ends with the container.
# HOME/TMPDIR live in an ext3 overlay image inside $TOAM (MATLAB needs file locks; /analysis NFS has none).
# raw/ is bound read-only inside the container.
# usage: ml_exec <tag> <matlab logfile> <matlab -batch command>   (prefix with /usr/bin/time, nice, ... as needed)
ml_exec() {
  local tag=$1 log=$2 cmd=$3
  local ov=$TOAM/tmp/overlays/$tag.img wd=$TOAM/tmp/apptainer/$tag
  guard "$ov" "$wd" "$log"
  mkdir -p "$wd" "$(dirname "$ov")" "$(dirname "$log")"
  [ -f "$ov" ] || apptainer overlay create --sparse --size 8192 "$ov" >&2 || return 2
  APPTAINERENV_TOAM=$TOAM apptainer exec --fakeroot --pid --cleanenv --contain --workdir "$wd" --overlay "$ov" \
    -B /misc/opt/matlab2026a:/misc/opt/matlab2026a:ro -B /misc/matlab:/misc/matlab:ro \
    -B "$TOAM:$TOAM" -B "$TOAM/raw:$TOAM/raw:ro" --pwd "$SPMP/matlab" "$MLIMG" \
    bash -c 'mkdir -p /ovl/home /ovl/tmp; export HOME=/ovl/home TMPDIR=/ovl/tmp TMP=/ovl/tmp TEMP=/ovl/tmp
      exec "$0" -c "$1" -nojvm -singleCompThread -logfile "$2" -batch "$3"' "$MLBIN" "$MLLIC" "$log" "$cmd"
}

# summed RSS (kB) of all descendants of a pid
tree_rss() { ps -eo pid=,ppid=,rss= | awk -v root="$1" '{p[$1]=$2; r[$1]=$3} END{n=0; for (q in p){x=q; while ((x in p) && x!=root && x>1) x=p[x]; if (x==root && q!=root) n+=r[q]} print n}'; }
