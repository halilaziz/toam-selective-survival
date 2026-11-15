function toam_first_level(spec_file)
% TOAM_FIRST_LEVEL  First-level GLM of the preregistered TOAM re-analysis (H2, H3) for one participant.
%
% Adapted from multi_session_first_level.m by Mirko Bristle and Tom Willems
% (github.com/TomW92/TOAM-fMRI, commit e257c25, fmri/1st_level/multi_session_first_level.m; CC BY 4.0).
% The model settings are theirs; "l.N" refers to the line of their file. The conditions, their onsets and the
% preregistered contrasts come from the JSON spec written by toam_analysis/glm_spec.py. Changes: ../CHANGES.md.
%
% Usage (SPM12 r7771 on the path, see run_first_level.m):  toam_first_level('/path/spec_sub-60601.json')

spec = jsondecode(fileread(spec_file));
outdir = spec.outdir;
sessions = as_cell(spec.sessions);

clear matlabbatch
fs = struct();
fs.dir = cellstr(outdir);                                                              % l.43-44
for s = 1:numel(sessions)
    S = sessions{s};
    files = cellstr(spm_select('ExtFPList', S.func_dir, S.scan_regex));               % contrast_multi_session.m l.100
    assert(~isempty(files{1}), 'no scans for session %d in %s', s, S.func_dir);
    fs.sess(s).scans = files;                                                          % l.54
    conds = as_cell(S.conditions);
    for k = 1:numel(conds)
        fs.sess(s).cond(k).name = conds{k}.name;                                       % l.59
        fs.sess(s).cond(k).onset = double(conds{k}.onsets(:));                         % l.60
        fs.sess(s).cond(k).duration = 0;                                               % l.61
        fs.sess(s).cond(k).tmod = 0;                                                   % l.62
        fs.sess(s).cond(k).pmod = struct('name', {}, 'param', {}, 'poly', {});        % l.63
    end
    fs.sess(s).multi = {''};                                                           % l.66
    fs.sess(s).regress = struct('name', {}, 'val', {});                               % l.67
    rp = cellstr(spm_select('FPList', S.func_dir, S.rp_regex));                       % l.68
    assert(numel(rp) == 1 && ~isempty(rp{1}), 'expected one motion file in %s', S.func_dir);
    fs.sess(s).multi_reg = rp;
    fs.sess(s).hpf = 128;                                                              % l.69
end
fs.timing.units = 'secs';                                                              % l.73
fs.timing.RT = spec.TR;                                                                % l.74
fs.timing.fmri_t = spec.nslices;                                                       % l.75
fs.timing.fmri_t0 = spec.nslices / 2;                                                  % l.76
fs.mthresh = -Inf;                                                                     % l.77
fs.fact = struct('name', {}, 'levels', {});                                           % l.78
fs.bases.hrf.derivs = [0 0];                                                           % l.79
fs.volt = 1;                                                                           % l.80
fs.global = 'None';                                                                    % l.81
mask = cellstr(spm_select('FPListRec', spec.preproc_dir, '^crossSessionWhiteandGreyMatterMask')); % setup_config.m l.159
assert(~isempty(mask{1}), 'NO mask image found');                                      % l.83
fs.mask = mask(1);                                                                     % l.84
fs.cvi = 'AR(1)';                                                                      % l.85
matlabbatch{1}.spm.stats.fmri_spec = fs;
matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(outdir, 'SPM.mat')};             % l.90-91
matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;                               % l.92

if isfolder(outdir), rmdir(outdir, 's'); end                                           % l.107-109
mkdir(outdir);                                                                         % l.110
save(fullfile(outdir, '1st_level'), 'matlabbatch');                                    % l.111
spm_jobman('run', matlabbatch);

%% Preregistered contrasts, by regressor name (TOAM change: the authors built their own set of contrasts)
load(fullfile(outdir, 'SPM.mat'), 'SPM');
names = SPM.xX.name;
cons = as_cell(spec.contrasts);
consess = {};
fid = fopen(fullfile(outdir, 'contrast_status.tsv'), 'w');
fprintf(fid, 'name\teligible\treason\n');
for c = 1:numel(cons)
    C = cons{c};
    fprintf(fid, '%s\t%d\t%s\n', C.name, C.eligible, C.reason);
    if ~C.eligible, continue; end
    W = as_cell(C.weights);
    vec = zeros(1, numel(names));
    for k = 1:numel(W)
        target = sprintf('Sn(%d) %s*bf(1)', W{k}.session, W{k}.condition);
        j = find(strcmp(names, target));
        assert(numel(j) == 1, 'regressor not found: %s', target);
        vec(j) = W{k}.weight;
    end
    consess{end + 1}.tcon = struct('name', C.name, 'weights', vec, 'sessrep', 'none'); %#ok<AGROW>
end
fclose(fid);
if ~isempty(consess)
    clear matlabbatch
    matlabbatch{1}.spm.stats.con.spmmat = {fullfile(outdir, 'SPM.mat')};               % l.96
    matlabbatch{1}.spm.stats.con.consess = consess;                                    % l.100-104
    matlabbatch{1}.spm.stats.con.delete = 1;                                           % l.97
    spm_jobman('run', matlabbatch);
end
load(fullfile(outdir, 'SPM.mat'), 'SPM');
fid = fopen(fullfile(outdir, 'contrasts.tsv'), 'w');
fprintf(fid, 'name\tcon\n');
if isfield(SPM, 'xCon')
    for i = 1:numel(SPM.xCon)
        fprintf(fid, '%s\t%s\n', SPM.xCon(i).name, SPM.xCon(i).Vcon.fname);
    end
end
fclose(fid);
fprintf('[toam_first_level] %s: %d sessions, %d contrasts written to %s\n', spec.sub, numel(sessions), numel(consess), outdir);
end

function c = as_cell(x)
% jsondecode gives a struct array when the elements share their fields, a cell array otherwise
if isempty(x), c = {}; elseif iscell(x), c = x; else, c = num2cell(x); end
end
