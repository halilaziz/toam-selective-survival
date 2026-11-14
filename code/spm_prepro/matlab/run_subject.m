function run_subject(subj)
% run_subject - TOAM adaptation (THOUGHTS project, 2026-11-13): runs the authors' SPM12
% preprocessing chain for ONE participant, in the order of the authors' fmri/preprocessing/prepro.sh:
%   smallFOV_preprocessing_1(subj)     slice timing + realign (estimate & reslice)
%   smallFOV_preprocessing_1s(subj)    segmentation, skull-stripped T1, grey+white mask
%   smallFOV_preprocessing_2(subj, 1)  coregistration, normalisation, smoothing (native 1 mm; MNI 6 and 3 mm)
% The authors started a new MATLAB per step; here the three steps share one MATLAB session
% (one licence checkout). SPM is initialised exactly as setup_config.m does
% (spm('Defaults','fMRI'); spm_jobman('initcfg')), plus cmdline mode, which matches the
% authors' "matlab -nodisplay" runs (no graphics windows).
% Inputs must already be in $TOAM/derivatives/spmMB/sub-<id>/preproc (prep_inputs.sh).
% Authors' code: github.com/TomW92/TOAM-fMRI @ e257c25 (CC BY 4.0); see ../README.md.

if ~isnumeric(subj), subj = str2double(regexprep(char(subj),'^sub-','')); end
toam = getenv('TOAM'); assert(~isempty(toam), 'TOAM environment variable is not set');
here = fileparts(mfilename('fullpath'));   % <TOAM>/code/spm_prepro/matlab
root = fileparts(here);                    % <TOAM>/code/spm_prepro

% SPM12 r7771 from TOAM only; drop any site SPM (e.g. /misc/opt/spm12 r7219) from the path
p = strsplit(path, pathsep); old = p(startsWith(p, '/misc/opt/spm') | startsWith(p, '/opt/matlab/spm'));
if ~isempty(old), rmpath(old{:}); end
addpath(fullfile(toam,'tools','spm12'));
spm('Defaults','fMRI'); spm_jobman('initcfg');
spm_get_defaults('cmdline', true);
global initspm; initspm = 1;               % setup_config.m skips its own (identical) initialisation
[v, r] = spm('Ver');
assert(strcmp(r,'7771'), 'expected SPM12 r7771, found %s r%s', v, r);
fprintf('[run_subject] sub-%d | %s r%s (%s) | MATLAB %s | threads %d\n', subj, v, r, which('spm'), version, maxNumCompThreads);

% the authors' scripts add ../functions relative to pwd, so start in preprocessing/
cd(fullfile(root,'preprocessing'));
steps = {@() smallFOV_preprocessing_1(subj), @() smallFOV_preprocessing_1s(subj), @() smallFOV_preprocessing_2(subj, 1)};
names = {'step1_slicetime_realign', 'step1s_segment_masks', 'step2_coreg_normalise_smooth'};
for k = 1:numel(steps)
    t0 = tic;
    fprintf('[run_subject] %s start %s\n', names{k}, char(datetime('now','Format','yyyy-MM-dd HH:mm:ss')));
    steps{k}();
    fprintf('[run_subject] %s done %s (%.1f min)\n', names{k}, char(datetime('now','Format','yyyy-MM-dd HH:mm:ss')), toc(t0)/60);
end
cfg = setup_config(subj);
fprintf('[run_subject] params: seq=%s TR=%.4g nslices=%d ref_slice=%.4g ms TA=%.4g res=%.2g\n', ...
    cfg.seq.seq{1}, cfg.params.TR, cfg.params.nslices, cfg.params.ref_slice, cfg.params.TA, cfg.params.res);
fprintf('[run_subject] sub-%d finished\n', subj);
end
