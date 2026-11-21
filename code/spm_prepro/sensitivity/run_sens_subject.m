function run_sens_subject(subj)
% RUN_SENS_SUBJECT  Sensitivity analysis (unregistered; qc_records/SENSITIVITY_COREG_PLAN.md): runs
% smallFOV_preprocessing_2_scannercoords for one participant in derivatives/spmMB_coregfix. SPM is initialised
% exactly as ../matlab/run_subject.m does. Inputs are copied beforehand by prepare_tree.sh.
if ~isnumeric(subj), subj = str2double(regexprep(char(subj),'^sub-','')); end
toam = getenv('TOAM'); assert(~isempty(toam), 'TOAM environment variable is not set');
here = fileparts(mfilename('fullpath'));   % <TOAM>/code/spm_prepro/sensitivity
root = fileparts(here);                    % <TOAM>/code/spm_prepro
p = strsplit(path, pathsep); old = p(startsWith(p, '/misc/opt/spm') | startsWith(p, '/opt/matlab/spm'));
if ~isempty(old), rmpath(old{:}); end
addpath(fullfile(toam,'tools','spm12'));
spm('Defaults','fMRI'); spm_jobman('initcfg');
spm_get_defaults('cmdline', true);
global initspm; initspm = 1;
[v, r] = spm('Ver');
assert(strcmp(r,'7771'), 'expected SPM12 r7771, found %s r%s', v, r);
addpath(here);
cd(fullfile(root,'preprocessing'));        % the authors' scripts add ../functions relative to pwd
t0 = tic;
fprintf('[run_sens_subject] sub-%d | %s r%s | start %s\n', subj, v, r, char(datetime('now','Format','yyyy-MM-dd HH:mm:ss')));
smallFOV_preprocessing_2_scannercoords(subj, 1);
fprintf('[run_sens_subject] sub-%d done (%.1f min)\n', subj, toc(t0)/60);
end
