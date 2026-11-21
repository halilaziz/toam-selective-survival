function smooth_s6(sub)
% SMOOTH_S6  fMRIPrep route for RQ3: 6-mm smoothing in SPM12 (r7771) of the uncompressed MNI152NLin2009cAsym BOLD
% of one participant (prefix s6), the kernel of the SPM route. SPM is initialised as in ../matlab/run_first_level.m.
toam = getenv('TOAM'); assert(~isempty(toam), 'TOAM environment variable is not set');
p = strsplit(path, pathsep); old = p(startsWith(p, '/misc/opt/spm') | startsWith(p, '/opt/matlab/spm'));
if ~isempty(old), rmpath(old{:}); end
addpath(fullfile(toam, 'tools', 'spm12'));
spm('Defaults', 'fMRI'); spm_jobman('initcfg'); spm_get_defaults('cmdline', true);
[v, r] = spm('Ver'); assert(strcmp(r, '7771'), 'expected SPM12 r7771, found %s r%s', v, r);
d = fullfile(toam, 'derivatives', 'fmriprep_spm', sub);
f = cellstr(spm_select('FPListRec', d, '^sub-.*_space-MNI152NLin2009cAsym_desc-preproc_bold\.nii$'));
assert(numel(f) == 3 && ~isempty(f{1}), 'expected 3 runs in %s', d);
clear matlabbatch
for k = 1:numel(f)
    matlabbatch{k}.spm.spatial.smooth.data = cellstr(spm_select('ExtFPList', fileparts(f{k}), ['^' spm_file(f{k}, 'filename') '$'], Inf)); %#ok<AGROW>
    matlabbatch{k}.spm.spatial.smooth.fwhm = [6 6 6];
    matlabbatch{k}.spm.spatial.smooth.dtype = 0;
    matlabbatch{k}.spm.spatial.smooth.im = 0;
    matlabbatch{k}.spm.spatial.smooth.prefix = 's6';
end
spm_jobman('run', matlabbatch);
fprintf('[smooth_s6] %s: %d runs smoothed\n', sub, numel(f));
end
