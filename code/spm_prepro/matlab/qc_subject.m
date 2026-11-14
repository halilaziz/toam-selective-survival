function qc_subject(subj)
% qc_subject - QC of one participant's SPM preprocessing (TOAM adaptation, THOUGHTS project, 2026-11-13).
% Reads the outputs in $TOAM/derivatives/spmMB/sub-<id>/preproc and changes nothing there.
% Writes only into $TOAM/derivatives/spmMB_qc/sub-<id>/ (outside the authors' spmMB/<sub>/preproc
% tree, so none of their spm_select patterns can pick these files up):
%   qc_files.tsv   one row per image: volumes, dim, voxel size, datatype, handedness, largest
%                  affine difference across volumes, world bounding box of the grid
%   qc_motion.tsv  realignment parameters per run: frames, max |translation| (mm), max |rotation| (deg),
%                  framewise displacement (Power, 50 mm radius)
%   qc_norm.tsv    normalised mean EPI per run (w<mean image>, written here with the authors' bb/voxel
%                  size and the session's y_ field): non-zero voxels, signal bounding box and centroid (mm),
%                  fraction inside SPM's TPM brain mask, r with SPM's EPI template; normalised T1:
%                  r with SPM's avg152T1; cross-session MNI mask; first/last s6w volume non-empty
% No events, responses, ratings or other outcomes are read.

if ~isnumeric(subj), subj = str2double(regexprep(char(subj),'^sub-','')); end
toam = getenv('TOAM'); assert(~isempty(toam), 'TOAM environment variable is not set');
sid = sprintf('sub-%d', subj);
P = fullfile(toam,'derivatives','spmMB',sid,'preproc');
Q = fullfile(toam,'derivatives','spmMB_qc',sid);
if ~exist(Q,'dir'), mkdir(Q); end
bb = [-90 -126 -72; 90 90 108];                      % authors' normalise bounding box
pt = readtable(fullfile(toam,'raw','ds006265','participants.tsv'),'FileType','text','Delimiter','\t');
if any(strcmp(pt.participant_id, sid)), res = 0.8; arm = 'hipp'; else, res = 1.1; arm = 'wb'; end
sess = {'ses-1','ses-2'};
fprintf('[qc] %s arm=%s res=%.1f\n', sid, arm, res);

%% A. headers and affines
F = fopen(fullfile(Q,'qc_files.tsv'),'w');
fprintf(F,'session\tfolder\tfile\tnvol\tdim\tvox_mm\tdtype\tdet_sign\tmax_affine_diff_across_vols\tgrid_min_mm\tgrid_max_mm\n');
for s = 1:2
    for fold = {'func','anat'}
        L = dir(fullfile(P, sess{s}, fold{1}, '*.nii'));
        for k = 1:numel(L)
            V = spm_vol(fullfile(L(k).folder, L(k).name));
            M = V(1).mat; d = V(1).dim; if numel(d) < 3, d(3) = 1; end
            vox = sqrt(sum(M(1:3,1:3).^2));
            md = 0;
            for t = 2:numel(V), md = max(md, max(abs(V(t).mat(:) - M(:)))); end
            [c1, c2, c3] = ndgrid([1 d(1)], [1 d(2)], [1 d(3)]);
            w = M * [c1(:) c2(:) c3(:) ones(8,1)]';
            fprintf(F,'%s\t%s\t%s\t%d\t%s\t%s\t%s\t%d\t%.4g\t%s\t%s\n', sess{s}, fold{1}, L(k).name, numel(V), ...
                mat2str(d), mat2str(round(vox,4)), spm_type(V(1).dt(1)), sign(det(M(1:3,1:3))), md, ...
                mat2str(round(min(w(1:3,:),[],2)',1)), mat2str(round(max(w(1:3,:),[],2)',1)));
        end
    end
end
fclose(F);

%% B. realignment parameters
F = fopen(fullfile(Q,'qc_motion.tsv'),'w');
fprintf(F,'session\trp_file\tframes\tnvol_ra\tmax_abs_trans_xyz_mm\tmax_abs_rot_xyz_deg\tFD_mean_mm\tFD_max_mm\tn_FD_gt_0.5\n');
for s = 1:2
    L = dir(fullfile(P, sess{s}, 'func', 'rp_*.txt'));
    for k = 1:numel(L)
        rp = load(fullfile(L(k).folder, L(k).name));
        ra = dir(fullfile(P, sess{s}, 'func', ['r' regexprep(L(k).name, '^rp_(.*)\.txt$', '$1') '.nii']));
        nra = NaN; if ~isempty(ra), nra = numel(spm_vol(fullfile(ra(1).folder, ra(1).name))); end
        fd = [0; sum(abs(diff(rp(:,1:3))),2) + 50*sum(abs(diff(rp(:,4:6))),2)];
        fprintf(F,'%s\t%s\t%d\t%d\t%s\t%s\t%.3f\t%.3f\t%d\n', sess{s}, L(k).name, size(rp,1), nra, ...
            mat2str(round(max(abs(rp(:,1:3))),2)), mat2str(round(max(abs(rp(:,4:6)))*180/pi,2)), mean(fd), max(fd), sum(fd > 0.5));
        fprintf('[qc] %s %s frames=%d trans=%s mm rot=%s deg FDmax=%.2f\n', sess{s}, L(k).name, size(rp,1), ...
            mat2str(round(max(abs(rp(:,1:3))),2)), mat2str(round(max(abs(rp(:,4:6)))*180/pi,2)), max(fd));
    end
end
fclose(F);

%% C-E. normalised images
tpm = spm_vol(fullfile(spm('dir'),'tpm','TPM.nii'));
epi = spm_vol(fullfile(spm('dir'),'toolbox','OldNorm','EPI.nii'));
t1t = spm_vol(fullfile(spm('dir'),'canonical','avg152T1.nii'));
F = fopen(fullfile(Q,'qc_norm.tsv'),'w');
fprintf(F,'check\tsession\titem\tvalue\n');
for s = 1:2
    y = dir(fullfile(P, sess{s}, 'anat', 'y_sub*.nii'));
    means = dir(fullfile(P, sess{s}, 'func', 'mean*.nii'));
    for k = 1:numel(means)
        clear mb
        mb{1}.spm.util.defs.comp{1}.def = {fullfile(y(1).folder, y(1).name)};
        mb{1}.spm.util.defs.comp{2}.idbbvox.vox = [res res res];
        mb{1}.spm.util.defs.comp{2}.idbbvox.bb = bb;
        mb{1}.spm.util.defs.out{1}.pull.fnames = {fullfile(means(k).folder, means(k).name)};
        mb{1}.spm.util.defs.out{1}.pull.savedir.saveusr = {Q};
        mb{1}.spm.util.defs.out{1}.pull.interp = 4;
        mb{1}.spm.util.defs.out{1}.pull.mask = 1;
        mb{1}.spm.util.defs.out{1}.pull.fwhm = [0 0 0];
        mb{1}.spm.util.defs.out{1}.pull.prefix = 'w';
        spm_jobman('run', mb);
        Vw = spm_vol(fullfile(Q, ['w' means(k).name]));
        Y = spm_read_vols(Vw);
        pos = isfinite(Y) & Y > 0;
        sv = sort(Y(pos)); thr = 0.1 * sv(max(1, round(0.98*numel(sv))));   % 10% of the 98th percentile
        idx = find(Y > thr);
        [i1, i2, i3] = ind2sub(size(Y), idx);
        xyz = Vw.mat * [i1 i2 i3 ones(numel(idx),1)]';
        wgt = Y(idx)';
        cen = (xyz(1:3,:) * wgt') / sum(wgt);
        inb = brainmask(tpm, xyz);
        te = sample(epi, xyz);
        okt = isfinite(te);
        r = pearson(Y(idx(okt)), te(okt));
        item = means(k).name;
        row(F, 'norm_mean_epi_grid', sess{s}, item, sprintf('dim=%s vox=%s', mat2str(Vw.dim), mat2str(round(sqrt(sum(Vw.mat(1:3,1:3).^2)),3))));
        row(F, 'norm_mean_epi_nonzero_vox', sess{s}, item, sprintf('%d (%.1f%% of grid)', nnz(pos), 100*nnz(pos)/numel(Y)));
        row(F, 'norm_mean_epi_signal_bbox_mm', sess{s}, item, sprintf('%s to %s', mat2str(round(min(xyz(1:3,:),[],2)')), mat2str(round(max(xyz(1:3,:),[],2)'))));
        row(F, 'norm_mean_epi_centroid_mm', sess{s}, item, mat2str(round(cen',1)));
        row(F, 'norm_mean_epi_frac_in_TPM_brain', sess{s}, item, sprintf('%.3f', mean(inb)));
        row(F, 'norm_mean_epi_r_EPI_template', sess{s}, item, sprintf('%.3f', r));
        fprintf('[qc] %s w%s nonzero=%d signal bbox %s..%s centroid %s inTPMbrain=%.3f r(EPI)=%.3f\n', sess{s}, item, nnz(pos), ...
            mat2str(round(min(xyz(1:3,:),[],2)')), mat2str(round(max(xyz(1:3,:),[],2)')), mat2str(round(cen',1)), mean(inb), r);
    end
    % normalised skull-stripped T1 vs avg152T1 (every 3rd voxel)
    wt = dir(fullfile(P, sess{s}, 'anat', 'wskullStripped*.nii'));
    if ~isempty(wt)
        Vt = spm_vol(fullfile(wt(1).folder, wt(1).name)); Y = spm_read_vols(Vt);
        [i1, i2, i3] = ndgrid(1:3:Vt.dim(1), 1:3:Vt.dim(2), 1:3:Vt.dim(3));
        xyz = Vt.mat * [i1(:) i2(:) i3(:) ones(numel(i1),1)]';
        a = Y(sub2ind(Vt.dim, i1(:), i2(:), i3(:)));
        b = sample(t1t, xyz);
        ok = isfinite(a) & isfinite(b) & (a ~= 0 | b > 0);
        row(F, 'norm_T1_r_avg152T1', sess{s}, wt(1).name, sprintf('%.3f', pearson(a(ok), b(ok))));
        fprintf('[qc] %s %s r(avg152T1)=%.3f\n', sess{s}, wt(1).name, pearson(a(ok), b(ok)));
    end
    % first and last volume of one s6w run per session
    s6 = dir(fullfile(P, sess{s}, 'func', 's6w*.nii'));
    if ~isempty(s6)
        V = spm_vol(fullfile(s6(1).folder, s6(1).name));
        a = spm_read_vols(V(1)); b = spm_read_vols(V(end));
        row(F, 's6w_first_last_nonzero_vox', sess{s}, s6(1).name, sprintf('%d / %d (of %d vols)', nnz(a > 0), nnz(b > 0), numel(V)));
    end
end
cm = dir(fullfile(P, 'crossSessionWhiteandGreyMatterMaskMNI*.nii'));
if ~isempty(cm)
    Vm = spm_vol(fullfile(cm(1).folder, cm(1).name)); Y = spm_read_vols(Vm);
    idx = find(Y > 0.5); [i1, i2, i3] = ind2sub(size(Y), idx);
    xyz = Vm.mat * [i1 i2 i3 ones(numel(idx),1)]';
    row(F, 'cross_session_mask', 'both', cm(1).name, sprintf('vox=%d dim=%s frac_in_TPM_brain=%.3f', numel(idx), mat2str(Vm.dim), mean(brainmask(tpm, xyz))));
end
fclose(F);
fprintf('[qc] %s done: %s\n', sid, Q);
end

function row(F, c, s, i, v)
fprintf(F, '%s\t%s\t%s\t%s\n', c, s, i, v);
end

function v = xyzvox(V, xyz)
% world mm (4 x n) -> voxel coordinates of image V (3 x n)
v = V.mat \ xyz; v = v(1:3,:);
end

function s = sample(V, xyz)
% trilinear sample of image V at world mm coordinates (4 x n); column vector, NaN outside
v = xyzvox(V, xyz);
s = spm_sample_vol(V, v(1,:), v(2,:), v(3,:), 1); s = s(:);
out = any(v < 1 | v > V.dim(:), 1); s(out) = NaN;
end

function r = pearson(a, b)
% base-MATLAB Pearson r (corr would check out a Statistics Toolbox licence)
c = corrcoef(double(a(:)), double(b(:))); r = c(1,2);
end

function inb = brainmask(tpm, xyz)
% GM + WM + CSF probability of SPM's TPM > 0.5 at the given world coordinates
pv = zeros(1, size(xyz,2)); vx = xyzvox(tpm(1), xyz);
for c = 1:3, pv = pv + spm_sample_vol(tpm(c), vx(1,:), vx(2,:), vx(3,:), 1); end
inb = pv > 0.5;
end
