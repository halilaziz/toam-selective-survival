import re, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = sys.argv[1]
import os
IMPL_NOTES = os.environ.get('IMPL_NOTES') == '1'  # implementation-notes paragraph, only if Halil accepts the defaults
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
for side in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
    setattr(sec, side, Cm(2.5))

def set_font(style, name='Times New Roman', size=12, bold=None, italic=None):
    style.font.name = name; style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None: style.font.bold = bold
    if italic is not None: style.font.italic = italic
    rpr = style.element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'): rf.set(qn(a), name)

normal = doc.styles['Normal']; set_font(normal)
pf = normal.paragraph_format
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; pf.line_spacing = 1.5; pf.space_after = Pt(6); pf.space_before = Pt(0)
for lvl, ital in ((1, False), (2, True)):
    st = doc.styles[f'Heading {lvl}']; set_font(st, bold=True, italic=ital)
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT; st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.space_before = Pt(12 if lvl == 1 else 6); st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True

TOK = re.compile(r'(\*\*.+?\*\*|\*.+?\*|~.+?~|\^.+?\^)')
def runs(p, text, size=None, font=None, bold=False):
    for part in TOK.split(text):
        if not part: continue
        b, i, sub, sup = bold, False, False, False
        if part.startswith('**'): part, b = part[2:-2], True
        elif part.startswith('*'): part, i = part[1:-1], True
        elif part.startswith('~'): part, sub = part[1:-1], True
        elif part.startswith('^'): part, sup = part[1:-1], True
        r = p.add_run(part); r.bold = b; r.italic = i or None
        if sub: r.font.subscript = True
        if sup: r.font.superscript = True
        if size: r.font.size = Pt(size)
        if font:
            r.font.name = font; r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), font)
    return p

def P(text, align=None, italic_all=False, size=None):
    p = doc.add_paragraph()
    if align: p.alignment = align
    runs(p, text, size=size)
    if italic_all:
        for r in p.runs: r.italic = True
    return p
def H(text, lvl): return doc.add_heading(text, level=lvl)

def cell_borders(tbl):
    tblPr = tbl._tbl.tblPr; b = OxmlElement('w:tblBorders')
    for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        x = OxmlElement(f'w:{e}'); x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), '4'); x.set(qn('w:space'), '0'); x.set(qn('w:color'), '000000'); b.append(x)
    tblPr.append(b)

def T(label, title, header, rows, widths):
    doc.add_paragraph()  # empty line before
    cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cap.paragraph_format.keep_with_next = True; cap.paragraph_format.line_spacing = 1.0
    runs(cap, f'**{label}.** {title}')
    t = doc.add_table(rows=1 + len(rows), cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False; t.style = doc.styles['Table Grid']
    for j, w in enumerate(widths):
        for row in t.rows: row.cells[j].width = Cm(w)
    for ri, vals in enumerate([header] + rows):
        for j, v in enumerate(vals):
            c = t.rows[ri].cells[j]
            p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.0; p.paragraph_format.space_after = Pt(0)
            runs(p, v, size=8, font='Calibri', bold=(ri == 0))
    tr = t.rows[0]._tr; trPr = tr.get_or_add_trPr(); h = OxmlElement('w:tblHeader'); h.set(qn('w:val'), 'true'); trPr.append(h)
    doc.add_paragraph()  # empty line after

def page_number_footer():
    p = sec.footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(); f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = 'PAGE'
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
    r._r.append(f1); r._r.append(it); r._r.append(f2); r.font.name = 'Times New Roman'; r.font.size = Pt(10)
page_number_footer()

def REF(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Cm(1.27); p.paragraph_format.first_line_indent = Cm(-1.27)
    runs(p, text)

# ---------------- content ----------------
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
runs(t, '**Selective survival or trace change? A preregistered, composition-controlled re-analysis of overnight retrieval effects in the TOAM 7T dataset**')
P('Preregistration for secondary data analysis, following the OSF template of Van den Akker et al. (2021). Final version, 17 November 2026, submitted for registration on OSF.', align=WD_ALIGN_PARAGRAPH.CENTER, italic_all=True)

H('Part 1. Study information', 1)
H('Background', 2)
P('When response categories are compared across delays, the two comparisons contain different items. Items forgotten overnight leave the remembered category and join the forgotten one, and the items still remembered after a delay are a stronger subset of those remembered earlier. If item strength is related to a neural measure, a difference between tests can therefore arise without any change inside individual memory traces. We call this selective survival, in contrast to trace change.')
P('Willems et al. (2025) report two overnight effects in the TOAM dataset. In the small-field-of-view arm, hippocampal-head responses to correctly guessed items were larger at the 24-hour category retrieval than at the 30-minute retrieval (C1; their Table S9: peaks at MNI −27, −16, −14, *T* = 4.62, and 39, −22, −12, *T* = 3.92, *p* < .001 uncorrected). In the table sources of the authors’ repository, neither cluster survives family-wise error (FWE) correction (peak *p*~FWE~ = .074 and .629). In the whole-brain arm, the difference between correct sure and correct guess responses was larger at 24 hours than at 30 minutes in several neocortical regions (C2; their Table S8), and three of these clusters survive cluster-level FWE correction.')
P('In both analyses, each trial’s category is set by the response at that test. The items guessed at 24 hours therefore include items that were remembered at 30 minutes, and the items rated sure at 24 hours are the stronger subset of those rated sure at 30 minutes. The authors report no analysis that holds item composition constant.')
H('Research questions', 2)
P('RQ1 asks whether the response categories change in item composition between the 30-minute and the 24-hour test, measured with an item-strength index that does not use the participant being analysed. RQ2 asks whether effect C1 is still present when item composition is held constant, or whether it is carried by items forgotten overnight. RQ3, a secondary question, asks whether effect C2 is present within items whose status did not change.')
H('Hypotheses', 2)
for h in ['H1a. Items guessed at 24 hours are more memorable, as indexed by *m* (Part 3), than items guessed at 30 minutes.',
          'H1b. Items rated sure at 24 hours are more memorable than items rated sure at 30 minutes.',
          'H1c. Items forgotten overnight (FO: sure or unsure at 30 minutes, guess at 24 hours) are more memorable than items guessed at both tests (SG).',
          'H2r (reproduction). In the hippocampal region of interest, correct-guess responses are larger at 24 hours than at 30 minutes when all items are included, as in C1.',
          'H2a (prediction of the trace-change account). The same difference is present within SG items, for which item composition is constant.',
          'H2b (prediction of the selective-survival account). At 24 hours, correct-guess responses are larger for FO items than for SG items.',
          'H3r and H3a (secondary). The C2 interaction is present when all items are included (H3r) and within items whose status did not change, that is, items rated sure at both tests (SS) and SG items (H3a).']:
    P(h)
P('The two accounts are not mutually exclusive. The main quantity of interest is the share of effect C1 that item composition explains.')

H('Part 2. Data description', 1)
H('Dataset', 2)
P('TOAM (Trajectory of a Memory Trace; Willems et al., 2025) is available on OpenNeuro under a CC0 licence (snapshot 1.0.2). It comprises two arms of 20 participants each (Table 1). The authors’ analysis code is available at github.com/TomW92/TOAM-fMRI (commit e257c25, CC BY 4.0).')
P('Both datasets can be downloaded without restriction; their identifiers are https://doi.org/10.18112/openneuro.ds006265.v1.0.2 and https://doi.org/10.18112/openneuro.ds006266.v1.0.2. The copy used for all analyses in this plan was downloaded on 12 November 2026, and every file (266 of 266) matched the SHA-256 checksum in its git-annex key. ds006265 had been accessed before, in September 2026, for the exploratory analyses described in Part 4.')
T('Table 1', 'The two arms of the TOAM dataset', ['Arm', 'OpenNeuro accession', 'Acquisition', '*N*', 'Git commit (tag 1.0.2)'],
  [['Small field of view (MTL slab)', 'ds006265', '7T, 0.8 mm', '20', '92120fb'],
   ['Whole brain', 'ds006266', '7T, 1.1 mm', '20', '4b88a2b']], [4.6, 3.0, 2.6, 1.2, 3.6])
H('Design', 2)
P('Participants learned 96 face–object associations once on Day 1, and a category retrieval followed each learning trial. Memory was tested with category retrieval 30 minutes after learning (Day 1; BIDS session 1, task retrieval) and again 24 hours later, after one night of sleep (Day 2; session 2, task forgetexp). On each retrieval trial, a face cue was followed by a two-alternative category question (organic or inorganic) and a confidence rating (sure, unsure or guess). On Day 2, each retrieval trial was followed by a two-alternative object recognition trial. All participants studied the same 96-item pool; the released event files contain 88 to 96 items per participant and 96 items in total.')
H('Codebook', 2)
P('The BIDS events.tsv files contain the columns onset, duration, trial_type and item. The trial_type field encodes the event (faceRecog, the 1,000-ms face cue; ret, the category question; retRating, the confidence rating; recog, the recognition trial) and the trial’s status at that test (sure, unsure or guess; correct or incorrect). Items are linked across tests by the item field.')

H('Part 3. Variables', 1)
H('Status variables', 2)
P('For each participant, item and test, we record the confidence rating (sure, unsure or guess) and whether the category choice was correct. Trajectory classes combine the two tests (Table 2). Other combinations are modelled but are not of interest.')
T('Table 2', 'Trajectory classes', ['Class', '30-minute test', '24-hour test'],
  [['SG (guessed at both tests)', 'guess', 'guess'], ['FO (forgotten overnight)', 'sure or unsure', 'guess'], ['SS (sure at both tests)', 'sure', 'sure']], [5.6, 4.4, 4.4])
H('Memorability index', 2)
P('The memorability index *m* is independent of the participant analysed. For item *i* and target participant *p*, *m* is the proportion of the other participants (both arms, up to 39) who gave a correct sure response to item *i* at the 30-minute test, among those with a valid 30-minute trial for *i*, z-scored across the target participant’s items. Secondary versions use the 24-hour test or the mean of the two tests.')
H('Neural variables', 2)
P('Neural variables are first-level general linear model (GLM) contrast estimates for the face-cue (faceRecog) events at retrieval, averaged within regions of interest (ROIs). The primary ROI for RQ2 consists of two 6-mm spheres at the published hippocampal peaks (MNI −27, −16, −14 and 39, −22, −12), averaged across hemispheres. These peaks were selected on the full-set contrast in the same data, so the full-set estimate is biased upward. That bias favours H2a and therefore makes the test of the selective-survival account conservative.')
P('The secondary ROI for RQ2 is the anatomical hippocampal head from the FreeSurfer 7 hippocampal subfield segmentation of each participant’s T1 image, warped to MNI space with the participant’s SPM12 deformation, as in the authors’ normalisation_spm.m. A participant is included only if at least 50% of the ROI voxels lie inside the slab’s field of view in both sessions. The ROIs for RQ3 are 6-mm spheres at the peaks of the three Table S8 clusters that survive cluster-level FWE correction (MNI −28, −44, 42; −38, −2, 22; and 32, 12, 36), averaged.')
H('Preprocessing and first-level models', 2)
P('The two claims were produced by different pipelines. For the small-field-of-view arm (C1, RQ2), the authors’ code, README and preprint all use SPM12. For the whole-brain arm (C2, RQ3), the README, the figure scripts and the preprint (fMRIPrep 20.2.3 with ICA-AROMA) indicate that the published maps, including Table S8, were computed from fMRIPrep data through first-level code that is not public, whereas the public first-level code reads SPM12 derivatives for both arms. SPM12 is therefore the primary pipeline for RQ2. For RQ3 we report both the SPM12 route, which reproduces the public code, and an fMRIPrep route (Part 5), which is closer to the published maps.')
P('The SPM12 pipeline follows the authors’ code (commit e257c25) with path changes only: slice-timing correction, realignment, coregistration of the functional images to the participant’s bias-corrected T1 image, normalisation through SPM12 unified segmentation, and smoothing with a 6-mm kernel. One SPM12 GLM per participant covers all sessions' + (' (see Implementation notes)' if IMPL_NOTES else '') + ', with an AR(1) model, a 128-s high-pass filter, six motion regressors and event duration 0. The only change to the authors’ model is that, at each test, the correct-guess faceRecog regressors are split by trajectory class (SG, FO, other) and, for RQ3, the correct-sure regressors are split in the same way (SS, other). All other regressors are unchanged. As in the authors’ code, the first level takes the middle of the repetition time as the microtime reference, whereas slice-timing correction references the middle slice in acquisition order; we keep this for comparability.')

H('Part 4. Knowledge of the data', 1)
P('In September 2026 we explored ds006265 in an exploratory study (Stage A). For behaviour, we computed accuracy at the two tests (.623 and .603), the number of items that changed status (589 of 1,847 item–participant pairs) and how each participant’s own 30-minute confidence predicted 24-hour survival; the last analysis used the participant’s own measure, was partly circular and was withdrawn. For the BOLD data, we attempted to register the slab to the T1 image, which failed with FLIRT and ANTs in our hands, and computed registration-free whole-slab pattern reliability across sessions (*n* = 14, ICC ≈ 0.08). We ran no univariate, ROI or condition analyses by response category.')
P('On 12 November 2026 we checked only the structure of the data (file counts, trial-type vocabulary and item identifiers). Between 12 November 2026 and the registration date we ran the SPM12 preprocessing for all 40 participants (completed on 15 November 2026) and checked preprocessing quality (number of volumes, motion parameters, normalisation overlap with the MNI template and coverage of the published peaks). No GLM was fitted, and no response category, accuracy or other outcome was used in these steps. The fMRIPrep preprocessing of the whole-brain arm is still running at registration. Between 15 and 17 November 2026 we wrote the analysis code and tested it on simulated data only. For this we inspected the structure of the released event files and of the authors’ public behavioural log files (column names, the trial-type vocabulary with response categories masked, and the layout of runs and trials). This incidentally showed that one participant has a missing response for one item at the 30-minute test, that the last trials of one participant’s 30-minute test are missing from the released events, and that the odd-even run has no public event file. No accuracy, confidence rating, trajectory class, count by response category or memorability value was computed.')
P('We have read the preprint (version 3), its code and its result tables (S8 to S11); the hypotheses concern those published effects. From Stage A we know that a participant’s own 30-minute status predicts their 24-hour status in ds006265. H1 instead uses *m*, which is computed from other participants. We have not computed *m*, and we have not computed any neural measure by response category or trajectory in either arm.')

H('Part 5. Analyses', 1)
H('Exclusions and quality control', 2)
P('Items are excluded as in the authors’ code: items wrong at immediate retrieval, wrong with a sure rating, or answered with the wrong button. Trials coded NA are also excluded. The authors’ list of trials removed for aborted acquisitions is not public; we use the events as released and report any difference in trial counts. A participant contributes to a neural contrast only if every regressor in that contrast has at least four trials, and *N* is reported for each test.')
P('Before any GLM is fitted, each participant’s normalised mean EPI is overlaid on the MNI template and on the participant’s normalised T1 image. Participants whose hippocampal region is visibly misaligned are excluded, and the images and decisions are archived. No participants are removed as outliers; as a robustness check, all tests are repeated with 20% trimmed means.')
H('RQ1', 2)
P('For each of the 40 participants we compute the difference in mean *m* between two item sets: guessed at 24 hours minus guessed at 30 minutes (H1a), sure at 24 hours minus sure at 30 minutes (H1b), and FO minus SG (H1c). These differences are tested against zero with one-sided one-sample *t* tests across participants, Holm-corrected across H1a to H1c. We report effect sizes *d*~z~ with 95% confidence intervals (CIs) and, as a secondary index, Jeffreys–Zellner–Siow Bayes factors with scale *r* = √2/2. Robustness checks use correct trials only and the secondary versions of *m*.')
H('RQ2', 2)
P('In the small-field-of-view arm (*N* ≤ 20) we compute three ROI contrast estimates per participant: 24-hour minus 30-minute correct guesses with all items (H2r), the same difference within SG items (H2a), and FO minus SG correct guesses at 24 hours (H2b). These are tested with one-sided one-sample *t* tests, Holm-corrected across H2a and H2b, with *d*~z~, 95% CIs and BF~10~ as a secondary index. The composition share is 1 − (H2a estimate / H2r estimate), with a 95% percentile bootstrap CI over participants (10,000 resamples). The decision rules for the primary ROI are given in Table 3.')
T('Table 3', 'Decision rules for RQ2 (primary ROI)', ['Result', 'Conclusion'],
  [['H2r not significant', 'Reproduction failed; all estimates are reported descriptively and no conclusion is drawn about trace change or selective survival'],
   ['H2r significant; H2a significant; H2b not significant', 'Trace change supported'],
   ['H2r significant; H2b significant; H2a not significant, with the H2a estimate less than half the H2r estimate', 'Selective survival supported'],
   ['H2r significant; H2a and H2b both significant', 'Mixed account'],
   ['Any other pattern', 'Inconclusive']], [7.6, 8.4])
H('RQ3', 2)
P('In the whole-brain arm (*N* ≤ 20) we estimate the C2 interaction with all items (H3r) and within SS and SG items (H3a). This analysis is for estimation only (*d*~z~, 95% CIs and composition share), without a decision rule, because few items are rated sure at both tests.')
H('Robustness: fMRIPrep pipeline', 2)
P('The whole-brain arm is preprocessed a second time with fMRIPrep 25.2.7, the latest stable release at registration (Docker digest sha256:bd222fba3a9f07d6ecaa680c412907945106b846a76cd4fbfd86e61667c435f8). Where they apply, we use the options of the authors’ fMRIPrep script: output spaces MNI152NLin2009cAsym and anat, single-band reference and T2-weighted images ignored, BOLD-to-T1 initialisation by registration, and FreeSurfer surface reconstruction. The MNI-space outputs are smoothed with a 6-mm kernel in SPM12, and the same first-level models are fitted with fMRIPrep’s six motion parameters. H3r and H3a are re-estimated with this pipeline.')
P('Because the published whole-brain maps came from fMRIPrep data, this route is the closer reproduction of C2, while the SPM12 route reproduces the authors’ public code. The RQ3 result is called robust if both pipelines give the same sign and each estimate lies inside the other’s 95% CI; otherwise both are reported and no conclusion is drawn from either pipeline alone. The published maps used fMRIPrep 20.2.3 with ICA-AROMA. AROMA has not been part of fMRIPrep since version 23, so differences from the published maps may also reflect the version and the absence of AROMA denoising. The small-field-of-view arm is not reprocessed, because fMRIPrep is designed for whole-brain acquisitions and our earlier attempts to register the 22-mm slab to the T1 image failed. The run uses at most four participants at a time on a shared server and starts after the SPM12 preprocessing.')
H('Sensitivity', 2)
P('With one-sided α = .05 and 80% power, the smallest detectable effects are *d*~z~ = 0.40 at *N* = 40, 0.58 at *N* = 20 and 0.63 at *N* = 17 (Table 4). The published hippocampal peak (*T*(18) = 4.62, *d*~z~ ≈ 1.0) is inflated by peak selection and does not survive FWE correction, so the neural tests may be underpowered. Estimates and CIs are reported whether or not they are significant.')
T('Table 4', 'Sensitivity of the planned tests', ['*N*', 'Smallest detectable *d*~z~ (80% power, one-sided α = .05)'],
  [['40 (RQ1)', '0.40'], ['20 (RQ2, RQ3)', '0.58'], ['17', '0.63']], [4.0, 9.0])
H('Exploratory analyses', 2)
P('Analyses labelled exploratory include results for each hemisphere separately, the other Table S8 peaks, unsure trials, the recognition test, representational similarity analyses, and trial-level mixed models with random effects for participants and items.')
if IMPL_NOTES:
    H('Implementation notes', 2)
    P('These notes were written before registration from the analysis code (tag preregistration), which was tested on simulated data only. (1) The odd-even run (task consolidation) has no public event file in either dataset, so its task regressor cannot be rebuilt; the first-level model therefore contains the learning run and the two retrieval runs. (2) Items excluded by the authors’ rules stay in the model as a separate regressor that enters no contrast, because the authors kept all trials in their model. (3) The all-items estimates (H2r, H3r) are the trial-count-weighted combinations of the split regressors; the four-trial rule applies to each split regressor in H2a, H2b and H3a, and to the combined count in H2r and H3r. (4) The authors’ optional exclusion of recognition responses faster than 100 ms is not applied, as in their default settings; the authors recovered some late immediate-retrieval responses from logs that are not public, so a few more items may be excluded here, and trial counts are compared with theirs where possible. (5) BF~10~ is the two-sided JZS Bayes factor; the one-sided BF~+0~ is reported alongside it. (6) The RQ3 agreement criterion is applied to *d*~z~ and its 95% CI. (7) Correct-sure trials are split by trajectory class only in the whole-brain arm (RQ3). (8) A participant whose sphere has no voxel inside the slab is missing for that contrast; the 50% coverage rule applies to the anatomical region.')
H('Deviations', 2)
P('Any deviation from this plan will be listed, with its reason, in a deviations table in the report.')
H('Software', 2)
P('Preprocessing uses SPM12 r7771 on MATLAB R2026a (26.1.0.3203278), run in the mathworks/matlab-deps:r2026a container on the Northwell server milner, and fMRIPrep 25.2.7 in Apptainer for the robustness pipeline. Statistical analyses use Python 3.13 in a project virtual environment, with package versions pinned and recorded at analysis time. Our code is at https://github.com/halilaziz/toam-selective-survival; the version at registration, including the analysis code tested on simulated data, is tagged preregistration, and an archive of it is attached to the registration.')
H('Use of AI tools', 2)
P('The study direction and the decision to re-test the TOAM claims came from the authors. A large language model (Claude, Anthropic) helped extract design details from the preprint and code and drafted the hypotheses, analysis plan and text. The authors reviewed, revised and approved this content and take responsibility for it.')

H('References', 1)
REF('Van den Akker, O. R., Weston, S., Campbell, L., Chopik, B., Damian, R., Davis-Kean, P., Hall, A., Kosie, J., Kruse, E., Olsen, J., Ritchie, S., Valentine, K. D., Van ’t Veer, A., & Bakker, M. (2021). Preregistration of secondary data analysis: A template and tutorial. *Meta-Psychology*, *5*. https://doi.org/10.15626/MP.2020.2625')
REF('Willems, T., Zervas, K., Brogli, L. S., Rabe, F., Federspiel, A., & Henke, K. (2025). *Neural traces of forgotten memories persist in humans and are behaviorally relevant* [Preprint, version 3]. bioRxiv. https://doi.org/10.1101/2025.06.02.656652')

z = doc.settings.element.find(qn('w:zoom'))
if z is not None and z.get(qn('w:percent')) is None: z.set(qn('w:percent'), '100')
doc.core_properties.title = 'TOAM preregistration (secondary data analysis)'
doc.core_properties.author = ''
doc.save(OUT)
words = sum(len(p.text.split()) for p in doc.paragraphs) + sum(len(c.text.split()) for t in doc.tables for row in t.rows for c in row.cells)
print('saved', OUT, '| words', words, '| tables', len(doc.tables), '| headings', sum(1 for p in doc.paragraphs if p.style.name.startswith('Heading')))
