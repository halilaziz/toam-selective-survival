# Site settings for the TOAM scripts. Copy this file to code/site.local.sh (not tracked) and edit the values.
# code/env.sh sources code/site.local.sh when it exists.
# export TOAM=/path/to/workspace              # optional; the default is the folder that contains code/
export SGE_QUEUE=all.q                        # Sun Grid Engine queue (or queue@host) for the batch jobs
export MLBIN=/opt/matlab/R2026a/bin/matlab    # MATLAB R2026a binary; it runs inside the matlab-deps container
export MLLIC=/opt/matlab/licenses/network.lic # MATLAB licence: a licence file, or port@server
export FSLIC=/opt/freesurfer/license.txt      # FreeSurfer licence file, needed by fMRIPrep
