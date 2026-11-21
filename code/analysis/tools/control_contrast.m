function control_contrast(spec_file)
% CONTROL_CONTRAST  Hypothesis-free checks after a pilot first level (not a preregistered test):
%   1. every session's last onset falls inside its scans (onset < nscan * TR);
%   2. the number of onsets per condition in SPM.mat equals the spec;
%   3. a t contrast of all face-cue (faceRecog) regressors against the implicit baseline, appended to SPM.mat as
%      'CONTROL all faceRecog > baseline'; prints the peak T, its MNI coordinates and the number of voxels with T > 5.
% A silent run or an onset error shows up here before the preregistered contrasts are read.
spec = jsondecode(fileread(spec_file));
load(fullfile(spec.outdir, 'SPM.mat'), 'SPM');
S = spec.sessions; if ~iscell(S), S = num2cell(S); end
for s = 1:numel(SPM.Sess)
    U = SPM.Sess(s).U; last = 0; nsp = 0; nmat = 0;
    C = S{s}.conditions; if ~iscell(C), C = num2cell(C); end
    for k = 1:numel(U)
        last = max([last; U(k).ons(:)]); nmat = nmat + numel(U(k).ons);
    end
    for k = 1:numel(C), nsp = nsp + numel(C{k}.onsets); end
    fprintf('[control] %s session %d: nscan %d, scan span %.1f s, last onset %.1f s, onsets SPM %d / spec %d -> %s\n', ...
        spec.sub, s, SPM.nscan(s), SPM.nscan(s) * spec.TR, last, nmat, nsp, ...
        string(last < SPM.nscan(s) * spec.TR && nmat == nsp));
end
names = SPM.xX.name;
idx = find(contains(names, 'faceRecog') & endsWith(names, '*bf(1)'));
vec = zeros(1, numel(names)); vec(idx) = 1 / numel(idx);
clear matlabbatch
matlabbatch{1}.spm.stats.con.spmmat = {fullfile(spec.outdir, 'SPM.mat')};
matlabbatch{1}.spm.stats.con.consess{1}.tcon = struct('name', 'CONTROL all faceRecog > baseline', 'weights', vec, 'sessrep', 'none');
matlabbatch{1}.spm.stats.con.delete = 0;
spm_jobman('run', matlabbatch);
load(fullfile(spec.outdir, 'SPM.mat'), 'SPM');
V = spm_vol(fullfile(spec.outdir, SPM.xCon(end).Vspm.fname));
[Y, XYZ] = spm_read_vols(V);
[mx, i] = max(Y(:));
fprintf('[control] %s: %d faceRecog regressors; peak T = %.2f at MNI [%.0f %.0f %.0f]; voxels with T > 5: %d\n', ...
    spec.sub, numel(idx), mx, XYZ(1, i), XYZ(2, i), XYZ(3, i), sum(Y(:) > 5));
end
