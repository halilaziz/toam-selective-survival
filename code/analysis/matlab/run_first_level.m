function run_first_level(spec_file)
% RUN_FIRST_LEVEL  Initialise SPM12 r7771 exactly as code/spm_prepro/matlab/run_subject.m does, then run
% toam_first_level(spec_file). Called by first_level.sh inside the matlab-deps container.
toam = getenv('TOAM'); assert(~isempty(toam), 'TOAM environment variable is not set');
p = strsplit(path, pathsep); old = p(startsWith(p, '/misc/opt/spm') | startsWith(p, '/opt/matlab/spm'));
if ~isempty(old), rmpath(old{:}); end
spm_dir = getenv('SPM12'); if isempty(spm_dir), spm_dir = fullfile(toam, 'tools', 'spm12'); end
addpath(spm_dir);
addpath(fileparts(mfilename('fullpath')));
spm('Defaults', 'fMRI'); spm_jobman('initcfg');
spm_get_defaults('cmdline', true);
[v, r] = spm('Ver');
assert(strcmp(r, '7771'), 'expected SPM12 r7771, found %s r%s', v, r);
fprintf('[run_first_level] %s | %s r%s | MATLAB %s\n', spec_file, v, r, version);
toam_first_level(spec_file);
end
