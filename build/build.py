#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PolypAtlas build script — generates the static site from step 1-4 outputs.
Run:  python3 build.py
Output: ../site/ (the site), data copied to ../site/data/ (downloads)
Every number rendered on the site is copied from the step reports / result files,
never invented. Caveats are rendered next to the data they qualify.

i18n: full EN/ZH bilingual support, default EN.
  - All user-facing strings live in STRINGS (key -> (en, zh)) below.
  - Pages are rendered with EN inline + data-i18n="key" markers; an inline script
    (I18N_SCRIPT) swaps to ZH from the embedded dictionary when
    localStorage['pa_lang'] == 'zh'. Persisted across pages/reloads.
  - data.js cohort records carry n_en / n_zh design strings for the dynamic gene page.
  - gene_app.js has its own GS dictionary for JS-generated strings and calls
    PA_langChanged to re-render results on language switch.
  - WORKING_NAME stays effective in both languages (renaming still a one-line change).
"""
import csv, json, os, shutil, re, html as _html
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(BASE))  # ~/workspace/sci-crswnp-resource
SITE = os.path.join(PROJ, "web", "site")
VERSION = "v1.3"
BUILD_DATE = date.today().isoformat()

# ================= i18n string registry: key -> (en, zh) =================
# DO NOT translate via these keys: gene symbols, GEO accessions, dataset titles,
# numbers, PMIDs, file names. Only user-facing copy lives here.
_STRINGS = {}
def _def(key, en, zh):
    _STRINGS[key] = (en, zh)
def en_of(key):
    return _STRINGS[key][0]
def dk(key):
    """data-i18n attribute marker."""
    return f'data-i18n="{key}"'

# --- nav / header / footer ---
_def("nav_home", "Home", "首页")
_def("nav_gene", "Gene query", "基因查询")
_def("nav_cohorts", "Cohorts &amp; datasets", "队列与数据集")
_def("nav_downloads", "Data downloads", "数据下载")
_def("nav_pathways", "Pathway query", "通路查询")
_def("nav_methods", "Methods &amp; limitations", "方法与限制")
_def("title_home", "Home", "首页")
_def("title_gene", "Gene query", "基因查询")
_def("title_cohorts", "Cohorts &amp; datasets", "队列与数据集")
_def("title_downloads", "Data downloads", "数据下载")
_def("title_pathways", "Pathway query", "通路查询")
_def("title_methods", "Methods &amp; limitations", "方法与限制")
_def("disc",
     "<b>Research use only</b>: This site is an integrated query resource for publicly "
     "available chronic rhinosinusitis with nasal polyps (CRSwNP) transcriptomic data, "
     "for research reference only. It does not provide clinical diagnosis, disease "
     "probability estimates, or treatment recommendations. All values come from uniform "
     "reanalysis of public data; known limitations of each cohort are annotated alongside the data.",
     "<b>研究用途声明</b>：本站为鼻息肉（CRSwNP）公开转录组数据的整合查询资源，仅供科研参考，"
     "不提供临床诊断、患病概率或治疗建议。所有数值均为公开数据的统一再分析结果，每个队列的已知限制均标注在数据旁。")
# footer pieces (name injected separately)
_def("foot_working", "(working name, renamable)", "（工作名称，可更名）")
_def("foot_build", "Build date", "构建日期")
_def("foot_src", "Data source: public GEO data (PMID/GEO links for each series on the \u2018Cohorts &amp; datasets\u2019 page)", "数据来源：GEO 公开数据（各系列见“队列与数据集”页的 PMID/GEO 链接）")
_def("foot_auth", "Authors/contact: [to be filled]", "作者/联系方式：[待填]")

# --- index ---
_def("idx_intro",
     "This resource curates all 66 human chronic rhinosinusitis / nasal polyp datasets in GEO "
     "one by one (30 in the core set), re-runs differential analysis uniformly for each eligible "
     "bulk cohort, annotates single-cell datasets with one unified cell-type vocabulary, organizes "
     "GeoMx spatial data by compartment, and aligns the three evidence layers. All results are "
     "queryable and downloadable online.",
     "本资源对 GEO 全部 66 个慢性鼻窦炎/鼻息肉人类数据集逐个策展（核心集 30），对合格的 bulk 队列逐个统一重跑差异分析、"
     "对单细胞数据集统一注释到一套细胞类型词表、对 GeoMx 空间数据按区室整理，与 bulk/单细胞三方对齐。所有结果均可在线查询与下载。")
_stat = [
    ("series_curated", "Curated GSE series", "策展 GSE 系列"),
    ("core", "Core set", "核心集"),
    ("samples", "Total census samples", "普查样本总数"),
    ("bulk_cohorts", "Bulk DE cohorts", "bulk 差异队列"),
    ("bulk_ev", "Bulk gene\u00d7cohort evidence", "bulk 基因×队列证据"),
    ("sc_ds", "Single-cell datasets", "单细胞数据集"),
    ("sc_cells", "Single cells", "单细胞（细胞数）"),
    ("sc_donors", "Single-cell donor units", "单细胞供体单元"),
    ("sp_roi", "Spatial ROIs", "空间 ROI"),
    ("sp_genes", "Spatial panel genes", "空间 panel 基因"),
    ("endotype", "Series with endotype labels", "自带内型标签系列"),
]
for _k, _e, _z in _stat:
    _def("stat_" + _k, _e, _z)
_def("idx_layers_h", "Three evidence layers", "三层证据")
_def("idx_bulk",
     "<b>Bulk</b>: per-cohort differential analysis across 16 cohorts (30 contrasts); "
     "evidence matrix of 19,266 protein-coding genes \u00d7 cohorts. Expression matrices are "
     "never merged across platforms \u2014 aggregation happens at the results level only "
     "(direction / effect size / significance).",
     "<b>Bulk</b>：16 个队列逐队列差异分析（30 个对比），19,266 蛋白编码基因×队列证据矩阵。跨平台不合并表达矩阵，只在结果层汇总（方向/效应量/显著性）。")
_def("idx_sc",
     "<b>Single-cell</b>: unified annotation of 10 datasets (25-class cell vocabulary); "
     "476,254 cells, 105 donor units; differential statistics at donor level (pseudobulk); "
     "17,631 genes \u00d7 41 contrasts.",
     "<b>单细胞</b>：10 个数据集统一注释（25 类细胞词表），476,254 细胞、105 供体单元；差异统计以供体为单位（pseudobulk），17,631 基因×41 对比。")
_def("idx_sp",
     "<b>Spatial</b>: GSE235714 GeoMx, 40 ROIs (CD45+ immune / PanCK+ epithelial compartments), "
     "1,480-gene CTA panel \u2014 donor-level differential analysis found zero FDR&lt;0.05 genes in "
     "either compartment, so the spatial layer serves as a compartment-localization/display layer, "
     "not an independent evidence layer; only descriptive values are shown, alongside compartment "
     "logFC and the confounding caveat.",
     "<b>空间</b>：GSE235714 GeoMx 40 ROI（CD45+ 免疫 / PanCK+ 上皮区室），1,480 基因 CTA panel——"
     "<b>供体级差异分析两区室 FDR&lt;0.05 均为 0</b>，空间层定位为区室定位/展示层，不作为独立证据层；只展示描述性值，见区室 logFC 与混杂声明。")
_def("idx_start_h", "Quick start", "快速开始")
_def("idx_start",
     "Look up a gene (e.g. CLC, IL33): <a href=\"gene.html\"><b>Gene query \u2192</b></a>; "
     "browse all datasets and known limitations: <a href=\"cohorts.html\"><b>Cohorts &amp; datasets \u2192</b></a>; "
     "bulk downloads: <a href=\"downloads.html\"><b>Data downloads \u2192</b></a>.",
     "查一个基因（如 CLC、IL33）：<a href=\"gene.html\"><b>基因查询页 \u2192</b></a>；"
     "浏览全部数据集与已知限制：<a href=\"cohorts.html\"><b>队列与数据集 \u2192</b></a>；"
     "批量取数：<a href=\"downloads.html\"><b>数据下载 \u2192</b></a>。")
_def("idx_honest",
     "<b>Honesty statement (please read before use)</b>: cohort designs differ substantially "
     "\u2014 tissue confounding (GSE198950), no healthy controls (GSE189690, GSE330761), weak signal "
     "from primary cultures (GSE69093), tonsil controls (GSE270953), AERD single arm (GSE196169), and more. "
     "Each cohort\u2019s limitations are annotated next to its data; the \u2018Cohorts &amp; datasets\u2019 page has the full table.",
     "<b>诚实声明（使用前请读）</b>：各队列的设计差异很大——组织混杂（GSE198950）、无健康对照（GSE189690、GSE330761）、"
     "原代培养弱信号（GSE69093）、扁桃体对照（GSE270953）、AERD 单臂（GSE196169）等。每个队列的限制标注在其数据旁，“队列与数据集”页有全表。")

# --- gene page (static part) ---
_def("gene_ph", "Enter gene symbol, e.g. CLC", "输入基因符号，如 CLC")
_def("gene_go", "Search", "查询")
_def("gene_quick", "Quick genes:", "常用基因：")

# --- cohorts page ---
_def("co_bulk_h", "Bulk differential-analysis cohorts (16)", "Bulk 差异分析队列（16）")
_def("co_th_id", "Series", "系列")
_def("co_th_contrast", "Primary contrast (case vs control)", "主对比（case vs control）")
_def("co_th_method", "Method", "方法")
_def("co_th_sig", "Genes with FDR&lt;0.05", "FDR&lt;0.05 基因数")
_def("co_th_note", "Notes / limitations", "备注 / 限制")
_def("co_th_cells", "Cells", "细胞数")
_def("co_th_donors", "Donors", "供体")
_def("co_th_design", "Design", "设计")
_def("co_sc_h", "Single-cell unified-annotation datasets (10)", "单细胞统一注释数据集（10）")
_def("co_sc_intro",
     "476,254 cells and 105 donor units in total; annotated to a unified 25-class cell vocabulary; "
     "differential statistics at donor level (pseudobulk).",
     "共 476,254 细胞、105 供体单元；注释到统一 25 类细胞词表；差异统计以供体为单位（pseudobulk）。")
_def("co_sp_h", "Spatial datasets (1)", "空间数据集（1）")
_def("co_sp_intro",
     "GeoMx DSP: 40 ROIs \u00d7 10 donors (CRSwNP 6 / controls 4); panel of 1,480 genes "
     "(Nanostring DSP Human CTA; measured, not whole-transcriptome).",
     "GeoMx DSP：40 ROI × 10（CRSwNP 6 / 对照 4）供体；panel 1,480 基因（Nanostring DSP Human CTA；实测，非全转录组）。")
_def("co_sp_lim", "\u26a0 Spatial layer limits:", "\u26a0 空间层限制：")
_def("co_other_h", "Other", "其他")
_def("co_o1",
     "11 pending series: each has named items to verify; below core standard, excluded from queries "
     "(see the curation report).",
     "待核集 11 个系列：每个都有具名待核项，未达到 core 标准，不进入查询（详见策展报告）。")
_def("co_o2",
     "25 excluded series: superseries parents, healthy in-vitro models, adjacent diseases "
     "(allergic rhinitis/asthma), non-expression omics, etc. \u2014 per-series reasons in the curation table.",
     "剔除 25 个系列：superseries 父记录、健康体外模型、邻近疾病（过敏性鼻炎/哮喘）、非表达组学等，逐条原因见策展表。")
_def("co_o3",
     "3 core ncRNA-array series (GSE169375/GSE169376/GSE32300): different molecule type; excluded "
     "from this round of bulk DE; results provided separately.",
     "3 个 ncRNA 阵列核心系列（GSE169375/GSE169376/GSE32300）：分子类型不同，本轮未进入 bulk DE；结果文件另行提供。")
_def("co_lim_label", "limitation:", "限制：")
_def("co_warn", "\u26a0 Limitation:", "\u26a0 限制：")

# --- downloads page ---
_dl = [
    ("dl_evlfc",
     "Bulk: logFC of 19,266 protein-coding genes \u00d7 16 cohorts (primary contrasts; probes collapsed by min-p).",
     "Bulk：19,266 蛋白编码基因 × 16 队列 logFC（主对比；探针按 min-p 塌缩）。"),
    ("dl_evfdr",
     "Bulk: BH-FDR for the same matrix.",
     "Bulk：同上矩阵的 BH-FDR。"),
    ("dl_dezip",
     "Bulk: full per-cohort differential results for 30 contrasts (symbol, logFC, p, FDR).",
     "Bulk：30 个对比的逐队列全量差异结果（symbol, logFC, p, FDR）。"),
    ("dl_runlog",
     "Bulk: record of n, scale verdicts, methods and status for 30 contrasts.",
     "Bulk：30 个对比的 n、尺度裁决、方法、状态记录。"),
    ("dl_panel",
     "Bulk: per-cohort values of the 8-gene positive-control panel (CLC/CCL26/CCL13/IL33/TSLP/POSTN/SERPINB2/ALOX15).",
     "Bulk：8 基因阳性对照 panel（CLC/CCL26/CCL13/IL33/TSLP/POSTN/SERPINB2/ALOX15）逐队列数值。"),
    ("dl_scev",
     "Single-cell: 17,631 genes \u00d7 41 cell-type-level pseudobulk contrasts (logFC+FDR).",
     "单细胞：17,631 基因 × 41 个细胞类型级 pseudobulk 对比（logFC+FDR）。"),
    ("dl_comp",
     "Single-cell: composition table of 1,431 rows (dataset \u00d7 donor \u00d7 group \u00d7 cell type \u00d7 fraction).",
     "单细胞：1,431 行 dataset×donor×group×celltype×fraction 组成表。"),
    ("dl_align",
     "Spatial: 1,480 panel genes \u00d7 39 columns (two spatial compartments + 16 bulk cohorts + same-study single-cell averages).",
     "空间：1,480 panel 基因 × 39 列（空间两区室 + 16 bulk 队列 + 同研究单细胞平均）。"),
    ("dl_roi",
     "Spatial: 40-ROI metadata (including QC flag GSM7508390).",
     "空间：40 ROI 元数据（含 QC 标记 GSM7508390）。"),
    ("dl_cur",
     "Master curation table: per-series grading of all 66 series (verdict / evidence notes).",
     "策展总表：66 个系列逐个定性（verdict/证据注记）。"),
    ("dl8_ora",
     "Analysis layer: over-representation enrichment for all contrasts (GO BP/CC/MF, Reactome, KEGG; up/down separately; low-DE directions skipped).",
     "分析层：全部对比的过表征富集（GO BP/CC/MF、Reactome、KEGG；上下调分开；DE 不足的方向已跳过）。"),
    ("dl8_gsea",
     "Analysis layer: GSEA for 62 adequately powered contrasts (Hallmark, GO-BP, Reactome, KEGG; 40 MB).",
     "分析层：62 个有功效对比的 GSEA（Hallmark、GO-BP、Reactome、KEGG；40 MB）。"),
    ("dl8_psc",
     "Analysis layer: per-sample ssGSEA program scores (13 programs \u00d7 16 bulk cohorts).",
     "分析层：样本级 ssGSEA 程序打分（13 程序 × 16 bulk 队列）。"),
    ("dl8_psm",
     "Analysis layer: per-cohort program case-vs-control summary.",
     "分析层：逐队列程序病例-对照汇总。"),
    ("dl8_dsc",
     "Analysis layer: per-sample immune abundance estimates (MCP-counter-style marker scoring).",
     "分析层：样本级免疫丰度估计（MCP-counter-style marker 打分）。"),
    ("dl8_dsm",
     "Analysis layer: per-cohort deconvolution group summary.",
     "分析层：逐队列去卷积分组汇总。"),
    ("dl8_can",
     "Consensus genes (disease-only, 825 up / 196 down) with known approved-drug target annotation.",
     "共识基因（disease-only，825 上 / 196 下）附已获批药物靶点标注。"),
    ("dl8_cen",
     "Consensus genes: pathway enrichment of the up/down lists.",
     "共识基因：上下调清单的通路富集。"),
    ("dl8_lr1",
     "Cell\u2013cell communication (CellChat, GSE235711): CRSwNP vs control interaction comparison.",
     "细胞间通讯（CellChat，GSE235711）：CRSwNP vs 对照互作比较。"),
    ("dl8_lr2",
     "Cell\u2013cell communication (CellChat, GSE235711): CRSsNP vs control interaction comparison.",
     "细胞间通讯（CellChat，GSE235711）：CRSsNP vs 对照互作比较。"),
]
for _k, _e, _z in _dl:
    _def(_k, _e, _z)
_def("dl_usage",
     "<b>Usage notes</b>: all files are products of uniform reanalysis; each file\u2019s generation "
     "protocol is on the \u2018Methods &amp; limitations\u2019 page; annotated h5ad objects are too large "
     "to host here (available from the authors on request).",
     "<b>使用说明</b>：所有文件均为统一再分析产出；每个文件的生成口径见“方法与限制”页；"
     "已注释的 h5ad 对象体积大，未放上本站（可联系作者获取）。")

# --- pathways page ---
_def("path_ph", "Search a pathway term, e.g. interleukin-4", "搜索通路名称，如 interleukin-4")
_def("path_go", "Search", "查询")
_def("path_intro",
     "Search pathway terms enriched (FDR&lt;0.05) across the analysis layer: "
     "over-representation analysis and GSEA for all 71 bulk and single-cell contrasts. "
     "Each hit shows where it was enriched (cohort / cell type) and the effect size.",
     "搜索分析层中富集（FDR&lt;0.05）的通路：全部 71 个 bulk 与单细胞对比的过表征分析与 GSEA。"
     "每个命中显示其富集位置（队列/细胞类型）与效应量。")
_def("path_note",
     "Only terms with FDR&lt;0.05 are indexed (8,866 terms, 33,116 hits). "
     "Pathway names are shown in English \u2014 they are database identifiers (GO / Reactome / KEGG / Hallmark).",
     "仅收录 FDR&lt;0.05 的通路（8,866 条，33,116 条命中）。通路名为数据库标识符（GO/Reactome/KEGG/Hallmark），以英文显示。")
_def("path_th_term", "Pathway term", "通路")
_def("path_th_db", "Database / collection", "数据库/集合")
_def("path_th_ev", "Enriched in", "富集所在")
_def("path_th_stat", "Effect / FDR", "效应/FDR")
_def("path_none", "No enriched term matches this query.", "无匹配的富集通路。")
_def("path_more", "More results truncated; refine the query.", "结果过多已截断，请细化查询。")

# --- cohort analysis blocks ---
_def("an_h", "Analysis layer", "分析层")
_def("an_enr", "Top enriched pathways (FDR&lt;0.05)", "富集通路 top（FDR&lt;0.05）")
_def("an_enr_ns", "No pathway reached FDR&lt;0.05 in this cohort.", "本队列无通路达到 FDR&lt;0.05。")
_def("an_prog", "Program scores: significant vs control (ssGSEA)", "程序打分：相对对照的显著变化（ssGSEA）")
_def("an_prog_ns", "No program reached FDR&lt;0.05 in this cohort.", "本队列无程序达到 FDR&lt;0.05。")
_def("an_prog_up", "up", "上调")
_def("an_prog_down", "down", "下调")
_def("an_deconv", "Immune cell abundance estimates", "免疫细胞丰度估计")
_def("an_deconv_lab",
     "MCP-counter-style marker scoring \u2014 abundance <b>estimates</b>, not cell counts "
     "(not official MCPcounter output).",
     "MCP-counter-style marker 打分——丰度<b>估计值</b>，不是细胞计数（非官方 MCPcounter 包输出）。")
_def("an_deconv_ns", "No population reached FDR&lt;0.05.", "无群体达到 FDR&lt;0.05。")
_def("an_det", "Full enrichment tables (downloads page)", "完整富集表（见下载页）")

# --- gene page: pathways & consensus block ---
_def("gpw_t", "Pathways &amp; consensus", "通路与共识")
_def("gpw_path", "Pathways containing this gene, enriched (FDR&lt;0.05) in \u22652 contrasts", "含该基因且在 \u22652 个对比中富集（FDR&lt;0.05）的通路")
_def("gpw_cons", "Consensus list", "共识基因清单")
_def("gpw_cons_up", "consensus UP (one of 825 genes up-regulated across cohorts)", "共识上调（跨队列上调 825 基因之一）")
_def("gpw_cons_down", "consensus DOWN (one of 196 genes down-regulated across cohorts)", "共识下调（跨队列下调 196 基因之一）")
_def("gpw_cons_no", "Not in the consensus list.", "不在共识基因清单中。")
_def("gpw_target", "Known drug target", "已知药物靶点")
_def("gpw_ncol", "contrasts", "对比数")

# --- v1.3: step-9 added-value layers (F1/F4/F3/F6) ---
_def("nav_treatment", "Treatment response", "治疗反应")
_def("title_treatment", "Treatment response", "治疗反应")
_def("g_f1_t", "Cross-cohort meta-analysis", "跨队列 Meta 分析")
_def("g_f1_combined", "Combined logFC (random effects)", "合并 logFC（随机效应）")
_def("g_f1_ci", "95% CI", "95% 置信区间")
_def("g_f1_p", "Combined p", "合并 p 值")
_def("g_f1_i2", "Heterogeneity I\u00b2", "异质性 I\u00b2")
_def("g_f1_k", "cohorts", "队列数")
_def("g_f1_method",
     "Random-effects meta-analysis (DerSimonian\u2013Laird) over the primary case\u2013control contrasts of 10 bulk cohorts; per-cohort SE from lfcSE or |logFC/t|. Shown only when \u22653 cohorts measured the gene.",
     "10 个 bulk 队列主病例-对照对比的随机效应 Meta 分析（DerSimonian\u2013Laird）；各队列标准误取自 lfcSE 或 |logFC/t|。基因在 \u22653 个队列中测得时才展示。")
_def("g_f1_forest", "Per-cohort forest plot (\u00b11.96 SE) + meta-analysis diamond", "各队列森林图（±1.96 SE）+ Meta 分析菱形")
_def("g_f4_t", "Top co-expressed genes", "高共表达基因")
_def("g_f4_method",
     "Spearman correlation across samples within each bulk cohort, Fisher-z averaged across \u22653 cohorts; top-10 positive partners restricted to evidence-matrix genes.",
     "各 bulk 队列内样本间 Spearman 相关，经 \u22653 队列 Fisher-z 合并；仅展示证据矩阵基因中的前 10 正相关伙伴。")
_def("g_f4_th_g", "Gene", "基因")
_def("g_f4_th_r", "Mean r", "平均 r")
_def("g_f4_th_k", "cohorts", "队列数")
_def("g_f3_t", "Genetic support", "遗传支持")
_def("g_f3_gwas", "GWAS Catalog (genome-wide significant, p\u22645e-8)", "GWAS Catalog（全基因组显著，p\u22645e-8）")
_def("g_f3_trait", "Trait", "性状")
_def("g_f3_bestp", "Strongest p", "最强 p 值")
_def("g_f3_n", "associations", "关联数")
_def("g_f3_eqtl", "GTEx v8 single-tissue eQTL presence", "GTEx v8 单组织 eQTL 存在性")
_def("g_f3_proxy",
     "\u26a0 GTEx has no nasal tissue data; Whole Blood / Lung / Skin are proxy tissues.",
     "\u26a0 GTEx 无鼻组织数据；全血 / 肺 / 皮肤为代理组织。")
_def("g_f3_method",
     "GWAS Catalog REST v2 queried for in-scope traits (CRSwNP, nasal polyps, chronic rhinosinusitis, asthma, allergic rhinitis, eosinophil counts); GTEx v8 checked for significant single-tissue eQTL presence.",
     "用 GWAS Catalog REST v2 查询范围内性状（CRSwNP、鼻息肉、慢性鼻窦炎、哮喘、过敏性鼻炎、嗜酸粒细胞计数）；GTEx v8 检查显著单组织 eQTL 存在性。")
_def("g_f6_t", "Literature support", "文献支持")
_def("g_f6_method",
     "Gene-level claims extracted verbatim from linked PubMed abstracts of the original papers and tested against our reanalysis; audited genes only (no extrapolation).",
     "基因水平声称逐字摘自原文关联 PubMed 摘要并用我们的重分析检验；仅限已审计基因（不外推）。")
_def("g_f6_claims", "published claims tested", "已发表声称已检验")
_def("g_f6_rep", "reproduced", "复现")
_def("g_f6_dir", "direction-consistent only", "仅方向一致")
_def("g_f6_not", "not reproduced", "未复现")
# --- v1.3: treatment page ---
_def("t_intro",
     "<b>Treatment response</b>: everything on this page comes from public treatment cohorts re-analyzed uniformly. The only clinical treatment cohort in the collection is the SINUS-52 dupilumab trial (GSE267331, paired pre/post nasal brushings).",
     "<b>治疗反应</b>：本页所有内容来自统一重分析的公开治疗队列。本集合中唯一的临床治疗队列是 SINUS-52 dupilumab 试验（GSE267331，配对治疗前后鼻刷）。")
_def("t_dup_h", "Dupilumab (SINUS-52, GSE267331)", "Dupilumab（SINUS-52，GSE267331）")
_def("t_dup_stats", "DE genes (FDR<0.05, paired)", "DE 基因（FDR<0.05，配对）")
_def("t_marker_h", "Type-2 marker reversal (post vs pre)", "2 型标志物逆转（治疗后 vs 前）")
_def("t_marker_note",
     "7/8 markers direction-correct per the DE file (CLC/POSTN/SERPINB2 significant); IL33 essentially flat (+0.016, FDR\u22481.0) and counted as not reversed. Placebo arm: 0 genes FDR<0.05.",
     "按 DE 文件 7/8 标志物方向正确（CLC/POSTN/SERPINB2 显著）；IL33 基本不动（+0.016，FDR\u22481.0）计为未逆转。安慰剂臂：0 基因 FDR<0.05。")
_def("t_prog_h", "Program-score changes (paired, post \u2212 pre)", "程序打分变化（配对，治疗后 − 治疗前）")
_def("t_prog_note",
     "ssGSEA-style estimates from paired samples (n=47); p from paired signed-rank test. Shown: all 13 programs; bold rows are FDR<0.05.",
     "配对样本的 ssGSEA-style 估计（n=47）；p 为配对符号秩检验。展示全部 13 个程序；加粗为 FDR<0.05。")
_def("t_inv_h", "Treatment contrasts in this collection", "本集合中的治疗相关对比")
_def("t_inv_note",
     "Only contrasts actually run are listed. No steroid, surgery, or other clinical treatment contrasts were run among the 30 bulk contrasts.",
     "仅列出实际跑过的对比。30 个 bulk 对比中没有类固醇、手术或其他临床治疗对比。")
_def("t_drug_h", "Drug reversal candidates (in-silico hypothesis generation)", "药物逆转候选（纯计算假说生成）")
_def("t_drug_method",
     "Consensus signature (825 up / 196 down genes) queried against L1000CDS2 for compounds that reverse the signature; reported scores are the L1000CDS2 overlap scores. These are computational hypotheses, not experimental evidence of efficacy.",
     "共识签名（825 上调 / 196 下调基因）在 L1000CDS2 中查询能逆转该签名的化合物；分数为 L1000CDS2  overlap 分数。这些是计算假说，非疗效实验证据。")
_def("t_cav",
     "\u26a0 Nasal brushing samples, not polyp tissue \u2014 cellular context differs from the polyp-resource core. Readout is marker-level mRNA reversal, not clinical endpoints (NPS, SNOT-22).",
     "\u26a0 鼻刷样本，非息肉组织——细胞构成与息肉资源核心不同。读数是标志物 mRNA 水平的逆转，非临床终点（NPS、SNOT-22）。")
# --- v1.3: downloads ---
_dl9 = [
    ("dl9_f1meta",
     "Meta-analysis: per-gene combined logFC, 95% CI, combined p, I\u00b2, k (DerSimonian\u2013Laird, 10 primary contrasts; genes with k\u22653).",
     "Meta 分析：逐基因合并 logFC、95% CI、合并 p、I\u00b2、k（DerSimonian\u2013Laird，10 个主对比；k\u22653 的基因）。"),
    ("dl9_f1coh",
     "Meta-analysis: per-cohort logFC and SE for the same genes (forest-plot input).",
     "Meta 分析：同上基因逐队列 logFC 与 SE（森林图输入）。"),
    ("dl9_f2",
     "Drug reversal: L1000CDS2 hits for the consensus signature (top 50; in-silico hypothesis generation only).",
     "药物逆转：共识签名的 L1000CDS2 命中（前 50；仅计算假说生成）。"),
    ("dl9_f3",
     "Genetic support: GWAS Catalog p\u22645e-8 hits and GTEx v8 eQTL presence per gene (proxy tissues noted).",
     "遗传支持：逐基因 GWAS Catalog p\u22645e-8 命中与 GTEx v8 eQTL 存在性（已注代理组织）。"),
    ("dl9_f4",
     "Co-expression: top-10 positive partners per gene (Fisher-z averaged Spearman over \u22653 bulk cohorts).",
     "共表达：逐基因前 10 正相关伙伴（\u22653 bulk 队列 Fisher-z 合并 Spearman）。"),
    ("dl9_f6",
     "Literature support: per-gene claim counts from the original-paper reproduction audit (audited genes only).",
     "文献支持：原文复现审计的逐基因声称计数（仅已审计基因）。"),
    ("dl9_f10",
     "Treatment response: GSE267331 dupilumab stats, marker reversal, program changes, contrast inventory (JSON).",
     "治疗反应：GSE267331 dupilumab 统计、标志物逆转、程序变化、对比清单（JSON）。"),
]

# --- methods page ---
_def("m_flow_h", "Workflow", "流程")
_mf = [
    ("m_f1",
     "<b>Census &amp; curation</b>: each of the 66 human CRS / nasal-polyp GEO series (census of 1 October 2026) was individually "
     "verified (tissue / grouping / platform / sample size) and graded core / pending / excluded with "
     "per-series evidence notes; endotype labels come only from deposited metadata, never inferred.",
     "<b>普查与策展</b>：GEO 人类 CRS/鼻息肉查询 66 系列（2026 年 10 月 1 日普查）逐个验明（组织/分组/平台/样本量），定级 core/pending/excluded，逐条有证据注记；内型标签只认 deposited metadata，不推测。"),
    ("m_f2",
     "<b>Uniform bulk reanalysis</b>: independent differential analysis per cohort (counts \u2192 DESeq2; "
     "continuous values \u2192 limma; paired designs \u2192 paired models), preceded by a three-way scale "
     "check; probes collapsed to symbols by min-p; cross-platform aggregation at the results level only "
     "\u2014 expression matrices are never merged.",
     "<b>Bulk 统一重分析</b>：逐队列独立差异分析（counts→DESeq2；连续值→limma；配对→配对模型），先做尺度三方核查；探针按 min-p 塌缩到 symbol；跨平台只在结果层汇总，不合并表达矩阵。"),
    ("m_f3",
     "<b>Unified single-cell annotation</b>: Leiden clustering + canonical marker scoring to a unified "
     "25-class vocabulary (scored on the full gene matrix, not an HVG subset); positive-control "
     "assertions (housekeeping / epithelial / immune markers) must pass before results are released; "
     "differential statistics at donor level (pseudobulk).",
     "<b>单细胞统一注释</b>：leiden 聚类 + 规范 marker 打分到统一 25 类词表（全基因矩阵打分，非 HVG 子集）；出结果前先过阳性对照断言（管家/上皮/免疫标志）；差异统计以供体为单位（pseudobulk）。"),
    ("m_f4",
     "<b>Spatial</b>: GeoMx organized by compartment; with 6-vs-4 donors no gene reaches FDR "
     "significance, so the spatial layer serves only as a compartment-localization/display layer, not "
     "independent evidence; descriptive values are shown with fixed annotations of low power and "
     "tissue confounding.",
     "<b>空间</b>：GeoMx 按区室整理；6v4 供体下 FDR 全为 0，故空间层只作区室定位/展示层，不做独立证据；展示描述性值并固定标注低功效与组织混杂。"),
    ("m_f5",
     "<b>Website</b>: precomputed results rendered as a static viewer; known limitations of each dataset "
     "are annotated next to the data.",
     "<b>网站</b>：预计算结果做成静态查看器；每处数据的已知限制标注在数据旁。"),
    ("m_f6",
     "<b>Analysis layer</b>: pathway enrichment (over-representation on up/down genes separately + GSEA on "
     "powered contrasts), per-sample ssGSEA program scores (13 immune/epithelial programs), MCP-counter-style "
     "immune deconvolution (labeled abundance estimates), and CellChat ligand\u2013receptor analysis of the "
     "flagship single-cell dataset.",
     "<b>分析层</b>：通路富集（上下调分别过表征 + 有功效对比 GSEA）、样本级 ssGSEA 程序打分（13 个免疫/上皮程序）、"
     "MCP-counter-style 免疫去卷积（明确标注为丰度估计）、旗舰单细胞数据集的 CellChat 配体\u2013受体分析。"),
]
for _k, _e, _z in _mf:
    _def(_k, _e, _z)
_def("m_lim_h", "Known limitations (full list)", "已知限制（全文）")
_ml = [
    ("m_l1",
     "Endotype (eosinophilic / non-eosinophilic) labels come from deposited metadata in only 6 series, "
     "most with small samples \u2014 this site does not predict tissue eosinophil counts; it only shows "
     "program-/gene-level evidence.",
     "内型（嗜酸/非嗜酸）标签只有 6 个系列自带 deposited metadata，且多为小样本——本站不做组织嗜酸计数的预测，只做程序/基因层面的证据展示。"),
    ("m_l2",
     "Six bulk cohorts have n\u22647 per group or low power (GSE72713, GSE150846, GSE174681, GSE330761, "
     "GSE36830, GSE194282) \u2014 their weight in the evidence matrix should be discounted.",
     "6 个 bulk 队列 n≤7/组或功效低（GSE72713、GSE150846、GSE174681、GSE330761、GSE36830、GSE194282），证据矩阵中权重应下调。"),
    ("m_l3",
     "GSE198950 has tissue confounding, GSE69093 a genuine weak signal, GSE189690/GSE330761 no healthy "
     "controls \u2014 cross-cohort comparisons must be stratified, never directly merged.",
     "GSE198950 组织混杂、GSE69093 真实弱信号、GSE189690/GSE330761 无健康对照——跨队列比较时需分层看，不可直接合并。"),
    ("m_l4",
     "GSE158277 (paired N-ERD, n=20): GEO has only a results table, no expression matrix \u2014 "
     "reanalysis was not possible; it can be added if raw data become available.",
     "GSE158277（配对 N-ERD，n=20）GEO 只有结果表无表达矩阵，未能重分析；若获原始数据可补入。"),
    ("m_l5",
     "Single-cell: sorted preparations (GSE179292/GSE324445/GSE270953/GSE255544, etc.) do not "
     "represent whole tissue; GSE324445\u2019s nominal sort disagrees with measured composition; "
     "GSE270953 uses tonsil controls; GSE276503 has only 2 controls.",
     "单细胞：分选制剂（GSE179292/GSE324445/GSE270953/GSE255544 等）组成不代表整组织；GSE324445 名义分选与实测组成不符；GSE270953 对照为扁桃体；GSE276503 对照仅 2 例。"),
    ("m_l6",
     "Spatial: see the four spatial-layer limitations on the \u2018Cohorts &amp; datasets\u2019 page.",
     "空间：见“队列与数据集”页的四条空间层限制。"),
    ("m_l7",
     "Secondary analysis of public data: ethics approval for the original studies rests with those "
     "studies; this site collects no new samples or personal information.",
     "公开数据二次分析：原始研究的伦理批准由各原始研究承担；本站不收集任何新样本与个人信息。"),
    ("m_l8",
     "Analysis layer: deconvolution values are abundance <b>estimates</b> (marker scoring), not cell counts; "
     "CellChat probabilities are small (~1e-6) and classical type-2 cytokine pairs fall below reliable "
     "single-cell detection, so no cytokine-pair claims are made.",
     "分析层：去卷积为丰度<b>估计值</b>（marker 打分），不是细胞计数；CellChat 概率很小（~1e-6），经典 2 型细胞因子"
     "对低于单细胞可靠检测线，故不作细胞因子互作声称。"),
]
for _k, _e, _z in _ml:
    _def(_k, _e, _z)
_def("m_src_h", "Data sources", "数据来源")
_def("m_src",
     "All data come from public GEO series (PMID and GEO links for each series are on the "
     "\u2018Cohorts &amp; datasets\u2019 page); the curation and reanalysis reports plus this site\u2019s "
     "build scripts are public with the code repository, so every number is reproducible.",
     "全部来自 GEO 公开系列（各系列 PMID 与 GEO 链接见“队列与数据集”页）；策展报告、重分析报告与本网站构建脚本随代码仓库公开，全部数字可复现。")
_def("m_auth_h", "Authors &amp; contact", "作者与联系")
_def("m_auth",
     "Authors: [to be filled] \u00b7 Corresponding: [to be filled] \u00b7 Cite this resource: [to be filled]",
     "作者：[待填] · 通讯：[待填] · 引用本资源：[待填]")

# ---------------- cohort metadata (from step2_report.md, numbers exact) --------
# n / n_en: design strings for the static cohorts page + dynamic gene page
# note / caveat (+ _en): shown next to the data (data-i18n keys generated below)
BULK_COHORTS = [
    {"id": "GSE136825", "n": "息肉(75) vs 对照下鼻甲(28)", "n_en": "Polyp (75) vs control inferior turbinate (28)", "method": "RNA-seq · DESeq2",
     "sig": "5,320", "note": "本宇宙最大的 CRSwNP bulk 队列；阳性对照 panel 行为正确（CLC +3.87）。",
     "note_en": "The largest CRSwNP bulk cohort in this collection; positive-control panel behaves correctly (CLC +3.87)."},
    {"id": "GSE179265", "n": "CRSwNP(17) vs 健康对照(7)", "n_en": "CRSwNP (17) vs healthy controls (7)", "method": "RNA-seq · DESeq2",
     "sig": "5,278", "note": "附加对比：美国 vs 日本息肉。阳性对照 7/8 显著上调（CLC +7.51）。",
     "note_en": "Additional contrast: US vs Japanese polyps. Positive controls 7/8 significantly up (CLC +7.51)."},
    {"id": "GSE338426", "n": "CRSwNP(14) vs 对照(8)", "n_en": "CRSwNP (14) vs controls (8)", "method": "RNA-seq · DESeq2",
     "sig": "2,273", "note": "内型标签（嗜酸/非嗜酸）来自 deposited metadata。CLC +7.97。",
     "note_en": "Endotype labels (eosinophilic/non-eosinophilic) from deposited metadata. CLC +7.97."},
    {"id": "GSE198950", "n": "CRSwNP(5) vs 非CRS(4)", "n_en": "CRSwNP (5) vs non-CRS (4)", "method": "RNA-seq · DESeq2",
     "sig": "3,141", "caveat": "组织混杂：病例为筛窦组织、对照为下鼻甲组织——IL33/POSTN 显著反向可能源于此，使用时必须注明。",
     "caveat_en": "Tissue confounding: cases are ethmoid tissue, controls are inferior turbinate — the significant reversal of IL33/POSTN may stem from this; must be stated when used."},
    {"id": "GSE267331", "n": "dupilumab 治疗后 vs 前（47 对配对）", "n_en": "Dupilumab post- vs pre-treatment (47 paired pairs)", "method": "芯片 · limma 配对",
     "sig": "4,856", "note": "唯一的治疗纵向队列（SINUS-52 鼻刷）：CLC/POSTN/SERPINB2 显著下调，符合治疗逆转预期；安慰剂臂 0 个显著。",
     "note_en": "The only treatment longitudinal cohort (SINUS-52 nasal brushing): CLC/POSTN/SERPINB2 significantly down, consistent with treatment reversal; 0 significant in the placebo arm."},
    {"id": "GSE189690", "n": "N-ERD(13) vs 非 N-ERD CRSwNP(13)", "n_en": "N-ERD (13) vs non-N-ERD CRSwNP (13)", "method": "RNA-seq · DESeq2",
     "sig": "12", "caveat": "无健康对照：仅疾病亚型对比，不参与病例-对照方向先验。",
     "caveat_en": "No healthy controls: disease-subtype contrast only; excluded from case–control directional priors."},
    {"id": "GSE313186", "n": "毒素暴露 CRS(10) vs 未暴露对照(10)", "n_en": "Toxin-exposed CRS (10) vs unexposed controls (10)", "method": "RNA-seq · DESeq2",
     "sig": "106", "note": "退伍军人部署暴露队列；肥大细胞表型。",
     "note_en": "Veteran deployment-exposure cohort; mast-cell phenotype."},
    {"id": "GSE213809", "n": "刺激后 NP-ILC2 vs 外周血 ILC2(14v14)", "n_en": "Stimulated NP-ILC2 vs peripheral-blood ILC2 (14v14)", "method": "RNA-seq · DESeq2",
     "sig": "4", "note": "分选 ILC2 亚群图谱型，非病例对照队列设计。",
     "note_en": "Sorted-ILC2 subset atlas; not a case–control design."},
    {"id": "GSE150846", "n": "鼻息肉 ILC2 vs 外周血 ILC2(3v3)", "n_en": "Nasal-polyp ILC2 vs peripheral-blood ILC2 (3v3)", "method": "芯片 · limma",
     "sig": "606", "note": "分选 ILC2 亚群图谱型；n 极小。",
     "note_en": "Sorted-ILC2 subset atlas; very small n."},
    {"id": "GSE174681", "n": "息肉 ASC vs 外周血 naive B(3v4)", "n_en": "Polyp ASC vs peripheral-blood naive B (3v4)", "method": "TMM · limma",
     "sig": "1,813", "note": "分选 B 细胞亚群图谱型，非病例对照队列设计。",
     "note_en": "Sorted B-cell subset atlas; not a case–control design."},
    {"id": "GSE330761", "n": "CRSwNP-MCTC vs CRSsNP-MCTC(3v3)", "n_en": "CRSwNP-MCTC vs CRSsNP-MCTC (3v3)", "method": "txi counts · voom",
     "sig": "443", "caveat": "无健康对照；分选肥大细胞亚群图谱型（3v3）。",
     "caveat_en": "No healthy controls; sorted mast-cell subset atlas (3v3)."},
    {"id": "GSE194282", "n": "鼻息肉(7) vs 对照(7)", "n_en": "Nasal polyps (7) vs controls (7)", "method": "芯片 · limma",
     "sig": "251", "note": "对照含肿瘤旁正常组织；样本量小，功效有限。",
     "note_en": "Controls include tumor-adjacent normal tissue; small sample size, limited power."},
    {"id": "GSE36830", "n": "CRSwNP(12) vs 钩突对照(6)", "n_en": "CRSwNP (12) vs uncinate-process controls (6)", "method": "芯片 · limma",
     "sig": "0", "note": "表达矩阵为线性尺度，已 log2(x+1) 转换；0 个 FDR 显著为数据本底。",
     "note_en": "Expression matrix was linear-scale, log2(x+1)-transformed; zero FDR-significant genes reflect the data background."},
    {"id": "GSE69093", "n": "病例 vs 对照（校正细胞类型）", "n_en": "Cases vs controls (cell-type-adjusted)", "method": "芯片 · limma+协变量",
     "sig": "0", "caveat": "原代培养细胞：全转录组 0 显著但 p 值富集于小 p 端，判为真实弱信号（非技术错误）。系列注册平台误标（Affymetrix），已按 Illumina HumanHT-12 v4 注释修正。",
     "caveat_en": "Primary cultured cells: zero transcriptome-wide significant genes but p-values enriched at the small-p end — judged a genuine weak signal (not a technical error). Series platform was mislabeled at registration (Affymetrix); corrected to Illumina HumanHT-12 v4 annotation."},
    {"id": "GSE70898_70900", "n": "息肉 T 细胞 vs 正常鼻黏膜 T 细胞(12v6)", "n_en": "Polyp T cells vs normal nasal-mucosa T cells (12v6)", "method": "芯片 · limma",
     "sig": "9,426", "note": "同研究跨系列（GSE70898+GSE70900）合并；短期 explant 培养；平台误标已修正。",
     "note_en": "Merged across two series of the same study (GSE70898+GSE70900); short-term explant culture; platform mislabeling corrected."},
    {"id": "GSE72713", "n": "CRSwNP(6) vs 正常对照(3)", "n_en": "CRSwNP (6) vs normal controls (3)", "method": "FPKM · limma",
     "sig": "129", "note": "n 极小（3/3/3）；lncRNA+mRNA 混合文件。",
     "note_en": "Very small n (3/3/3); mixed lncRNA+mRNA files."},
]
BULK_IDS = [c["id"] for c in BULK_COHORTS]

SC_DATASETS = [
    {"id": "GSE235711", "cells": "55,827", "donors": "20", "design": "对照5 / CRSsNP5 / CRSwNP10",
     "design_en": "Controls 5 / CRSsNP 5 / CRSwNP 10",
     "note": "Liao Immunity 2025；完整组织图谱。CRSsNP vs 对照在供体水平几乎无显著基因（5v5，数据本底，非分析失败）。",
     "note_en": "Liao Immunity 2025; complete tissue atlas. CRSsNP vs controls has almost no donor-level significant genes (5v5, data background, not an analysis failure)."},
    {"id": "GSE276503", "cells": "177,666", "donors": "29 供体单元", "donors_en": "29 donor units", "design": "对照2 / CRSwNP27",
     "design_en": "Controls 2 / CRSwNP 27",
     "caveat": "对照仅 2 例（统计慎用）；4 个样本的存放端矩阵损坏已剔除；供体结构未声明。",
     "caveat_en": "Only 2 controls (use statistics with caution); 4 samples\u2019 matrices corrupted at the source and excluded; donor structure not declared."},
    {"id": "GSE270953", "cells": "51,926", "donors": "10", "design": "息肉5 / 扁桃体5",
     "design_en": "Polyps 5 / tonsils 5",
     "caveat": "对照为扁桃体（免疫学上与鼻黏膜差异大），解读须加 caveat；CITE-seq 臂未处理。",
     "caveat_en": "Controls are tonsils (immunologically distinct from nasal mucosa); interpret with this caveat; CITE-seq arm not processed."},
    {"id": "GSE249159", "cells": "42,041", "donors": "6", "design": "息肉3 / 外周血3",
     "design_en": "Polyps 3 / peripheral blood 3",
     "note": "小鼠臂已排除；仅 CD4_T 满足 3v3 DE 条件。",
     "note_en": "Mouse arm excluded; only CD4_T meets the 3v3 DE requirement."},
    {"id": "GSE196169", "cells": "37,168", "donors": "13", "design": "AERD 单臂",
     "design_en": "AERD single arm",
     "caveat": "存放数据无 CRSwNP 对照臂，已降级为单臂组成图谱；网站不列出该对比。",
     "caveat_en": "Deposited data has no CRSwNP control arm; downgraded to a single-arm composition atlas; this contrast is not listed on the site."},
    {"id": "GSE202100", "cells": "38,514", "donors": "5", "design": "CRSwNP 单臂（上皮刷检）",
     "design_en": "CRSwNP single arm (epithelial brushing)",
     "note": "tuft 信号（POU2F3/TRPM5）富集于 ionocyte 簇，未强行拆分，如实标注。",
     "note_en": "Tuft signal (POU2F3/TRPM5) enriched in the ionocyte cluster; not forcibly split, annotated as-is."},
    {"id": "GSE324445", "cells": "30,954", "donors": "10", "design": "息肉6 / 外周血4",
     "design_en": "Polyps 6 / peripheral blood 4",
     "caveat": "名义“分选 ILC2”，实测仅 36% 为真 ILC2、56% 为 CD4_T——网站展示实测组成，不用名义值。",
     "caveat_en": "Nominally \u2018sorted ILC2\u2019; measured only 36% true ILC2 and 56% CD4_T \u2014 the site shows measured composition, not the nominal label."},
    {"id": "GSE255544", "cells": "20,394", "donors": "7", "design": "CRSwNP 疾病单臂（淋巴细胞）",
     "design_en": "CRSwNP single arm (lymphocytes)",
     "note": "待核→转正（GSM 标题证实 CRSwNP，PMID 38589618）。",
     "note_en": "Pending \u2192 promoted to core (GSM titles confirm CRSwNP, PMID 38589618)."},
    {"id": "GSE156285", "cells": "10,803", "donors": "4", "design": "CRS 疾病单臂组成图谱",
     "design_en": "CRS single-arm composition atlas",
     "note": "旧版 10x 注释缺若干上皮 marker，部分簇只能标 ambiguous。",
     "note_en": "Older 10x annotation lacks several epithelial markers; some clusters can only be labeled ambiguous."},
    {"id": "GSE179292", "cells": "10,961", "donors": "4", "design": "CRSwNP 分选 T 细胞组成图谱",
     "design_en": "CRSwNP sorted-T-cell composition atlas",
     "note": "分选 T 细胞制剂。",
     "note_en": "Sorted T-cell preparation."},
]

SPATIAL_INFO = {
    "id": "GSE235714", "roi": 40, "donors": "10（CRSwNP 6 / 对照 4）",
    "donors_en": "10 (CRSwNP 6 / controls 4)",
    "panel": "1,480 基因（Nanostring DSP Human CTA；实测，非全转录组）",
    "panel_en": "1,480 genes (Nanostring DSP Human CTA; measured, not whole-transcriptome)",
    "caveats": [
        ("供体级差异分析两区室 FDR<0.05 均为 0——空间层为“区室定位/展示层”，不是疾病差异的独立证据层；只展示描述性区室 logFC，不做一致性声称。",
         "Donor-level differential analysis finds zero FDR<0.05 genes in either compartment \u2014 the spatial "
         "layer is a compartment-localization/display layer, not an independent evidence layer for disease "
         "differences; only descriptive compartment logFC values are shown, with no concordance claims."),
        ("疾病与组织完全混杂：CRSwNP 供体全为鼻息肉组织，对照全为筛窦组织。",
         "Disease is fully confounded with tissue: all CRSwNP donors are polyp tissue, all controls are ethmoid tissue."),
        ("GSM7508390（CRSwNP_8 CD45+ ROI2）QC 标记 'Low Surface Area'（保留未剔除）。",
         "GSM7508390 (CRSwNP_8 CD45+ ROI2) flagged \u2018Low Surface Area\u2019 in QC (retained, not removed)."),
        ("panel 覆盖率：bulk top100 基因并集仅 14.6% 在 panel 中；不在 panel 的基因（如 CLC/CCL26/POSTN/ALOX15）明确返回“不在 CTA panel 中”。",
         "Panel coverage: only 14.6% of the union of bulk top-100 genes is in the panel; genes not in the panel "
         "(e.g. CLC/CCL26/POSTN/ALOX15) explicitly return \u2018not in the CTA panel\u2019."),
    ],
}

# register data-driven note/caveat strings into the i18n dict (keys reused by
# cohorts.html AND the dynamic gene page, so both languages show the same text)
for _c in BULK_COHORTS:
    if _c.get("note"):
        _def("note_" + _c["id"], _c["note_en"], _c["note"])
    if _c.get("caveat"):
        _def("cav_" + _c["id"], _c["caveat_en"], _c["caveat"])
    _def("n_" + _c["id"], _c["n_en"], _c["n"])  # cohort design strings (bulk)
for _d in SC_DATASETS:
    if _d.get("note"):
        _def("sc_note_" + _d["id"], _d["note_en"], _d["note"])
    if _d.get("caveat"):
        _def("sc_cav_" + _d["id"], _d["caveat_en"], _d["caveat"])
    _def("sc_design_" + _d["id"], _d["design_en"], _d["design"])
    if "donors_en" in _d:
        _def("sc_donors_" + _d["id"], _d["donors_en"], _d["donors"])
for _i, (_zh, _en) in enumerate(SPATIAL_INFO["caveats"]):
    _def(f"sp_cav_{_i}", _en, _zh)

# gene_app.js dynamic strings (JS-side dictionary)
_def("g_empty", "Please enter a gene symbol.", "请输入基因符号。")
_def("g_notfound", "No match for", "未找到")
_def("g_suggest", "Did you mean:", "可能：")
_def("g_nosim", "No similar symbols.", "无相似符号。")
_def("g_bulk_t", "Bulk: 16 cohorts (primary contrasts)", "Bulk：16 队列（主对比）")
_def("g_th_cohort", "Cohort", "队列")
_def("g_th_contrast", "Contrast (dataset \u00b7 cell type \u00b7 design)", "对比（数据集 · 细胞类型 · 设计）")
_def("g_th_comp", "Compartment", "区室")
_def("g_th_desc", "logFC (donor-level, descriptive)", "logFC（供体级描述值）")
_def("g_limit_badge", "\u26a0 limit below", "\u26a0 限制见下")
_def("g_bulk_chart", "Bulk logFC bar chart", "Bulk logFC 条形图")
_def("g_sc_t", "Single-cell: cell-type-level contrasts", "单细胞：细胞类型级对比")
_def("g_bulk_nm", "This gene is not in the bulk evidence matrix (not measured).", "该基因不在 bulk 证据矩阵中（未测得）。")
_def("g_sc_nm", "This gene is not in the single-cell evidence matrix (not measured).", "该基因不在单细胞证据矩阵中（未测得）。")
_def("g_sp_t", "Spatial (GeoMx, GSE235714)", "空间（GeoMx，GSE235714）")
_def("g_cd45", "CD45+ immune compartment", "CD45+ 免疫区室")
_def("g_panck", "PanCK+ epithelial compartment", "PanCK+ 上皮区室")
_def("g_sp_cav",
     "\u26a0 Spatial layer limits: donor-level FDR&lt;0.05 is zero in both compartments (6 vs 4 donors); "
     "these are descriptive values, not independent evidence; disease and tissue are fully confounded "
     "(CRSwNP = polyp tissue vs controls = ethmoid tissue).",
     "\u26a0 空间层限制：两区室供体级 FDR&lt;0.05 均为 0（6v4 供体），此为描述性值，非独立证据；"
     "且疾病与组织完全混杂（CRSwNP=息肉组织 vs 对照=筛窦组织）。")
_def("g_notpanel",
     "This gene is <b>not in the GeoMx CTA panel (1,480 genes)</b> \u2014 no spatial data, not a missing value.",
     "该基因<b>不在 GeoMx CTA panel（1,480 基因）中</b>——无空间数据，非缺失值。")
_def("g_lim_colon", "limitation:", "限制：")

QUICK_GENES = ["CLC", "CCL26", "CCL13", "IL33", "TSLP", "POSTN", "SERPINB2", "ALOX15",
               "EPAS1", "PTGS2", "BIRC3", "S100A8"]

HEADLINE = {
    "series_curated": 66, "series_core": 30, "samples_curated": "2,046",
    "bulk_cohorts": 16, "bulk_genes": "19,266", "bulk_contrasts": 30,
    "sc_datasets": 10, "sc_cells": "476,254", "sc_donors": 105, "sc_genes": "17,631", "sc_contrasts": 41,
    "spatial_roi": 40, "spatial_donors": 10, "spatial_genes": "1,480",
    "endotype_series": 6, "treatment_cohort": "GSE267331（SINUS-52）",
}

# ---------------- helpers -----------------------------------------------
def f3(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return float(f"{v:.3f}")

def f4g(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return float(f"{v:.4g}")

def read_csv_dict(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def i18n_json():
    """Embedded dictionary for both languages, key -> {en, zh}."""
    return json.dumps({k: {"en": v[0], "zh": v[1]} for k, v in _STRINGS.items()},
                      ensure_ascii=False, separators=(",", ":"))

# ---------------- build gene data ---------------------------------------
def build_gene_data():
    s2 = os.path.join(PROJ, "analysis", "step2_bulk")
    s3 = os.path.join(PROJ, "analysis", "step3_scrna")
    s4 = os.path.join(PROJ, "analysis", "step4_spatial")

    # bulk logFC + FDR
    lfc_rows = read_csv_dict(os.path.join(s2, "evidence_matrix_logFC.csv"))
    fdr_rows = read_csv_dict(os.path.join(s2, "evidence_matrix_FDR.csv"))
    lfc_map = {r[""]: r for r in lfc_rows}
    fdr_map = {r[""]: r for r in fdr_rows}

    # sc contrasts
    sc_cols = open(os.path.join(s3, "celltype_evidence_matrix.csv"), encoding="utf-8").readline().rstrip("\n").split(",")
    contrasts = []
    for c in sc_cols[1:]:
        if c.endswith("__logFC"):
            base = c[:-len("__logFC")]
            contrasts.append(base)
    contrast_fdr = {b: b + "__FDR" for b in contrasts}

    def sc_label(base):
        # e.g. GSE235711:CD4_T:CRSsNP_vs_control -> (GSE235711, CD4_T, CRSsNP vs control)
        parts = base.split(":")
        ds = parts[0]
        ct = parts[1] if len(parts) > 1 else ""
        comp = parts[2] if len(parts) > 2 else ""
        return f"{ds} · {ct} · {comp.replace('_vs_', ' vs ')}"

    sc_rows = read_csv_dict(os.path.join(s3, "celltype_evidence_matrix.csv"))
    sc_map = {r["gene"]: r for r in sc_rows}

    # spatial
    sp_rows = read_csv_dict(os.path.join(s4, "alignment_table.csv"))
    sp_map = {r["gene"]: r for r in sp_rows}

    genes = {}
    union = set(lfc_map) | set(sc_map) | set(sp_map)
    for g in union:
        rec = {}
        b = []
        if g in lfc_map:
            lf, fd = lfc_map[g], fdr_map.get(g, {})
            for cid in BULK_IDS:
                lv, fv = f3(lf.get(cid)), f4g(fd.get(cid))
                b.append([lv, fv] if lv is not None else None)
            rec["b"] = b
        s = {}
        if g in sc_map:
            row = sc_map[g]
            for i, base in enumerate(contrasts):
                lv, fv = f3(row.get(base + "__logFC")), f4g(row.get(base + "__FDR"))
                if lv is not None:
                    s[i] = [lv, fv]
            if s:
                rec["s"] = s
        if g in sp_map:
            row = sp_map[g]
            lv1, fv1 = f3(row.get("sp_CD45_logFC")), f4g(row.get("sp_CD45_FDR"))
            lv2, fv2 = f3(row.get("sp_PanCK_logFC")), f4g(row.get("sp_PanCK_FDR"))
            if lv1 is not None or lv2 is not None:
                rec["sp"] = [lv1, fv1, lv2, fv2]
        genes[g] = rec
    return genes, [sc_label(b) for b in contrasts], len(union)

# ---------------- step8 analysis-layer loaders --------------------------------
def _fdr_ok(x):
    try:
        return float(x) < 0.05
    except (TypeError, ValueError):
        return False

def load_step8():
    s8 = os.path.join(PROJ, "analysis", "step8_expansion")
    ora = read_csv_dict(os.path.join(s8, "enrichment", "enrichment_ora.csv"))
    gsea = read_csv_dict(os.path.join(s8, "enrichment", "enrichment_gsea.csv"))
    psum = read_csv_dict(os.path.join(s8, "programs", "program_summary.csv"))
    dsum = read_csv_dict(os.path.join(s8, "deconv", "deconv_summary.csv"))
    cons = {}
    for r in read_csv_dict(os.path.join(s8, "consensus_annotated.csv")):
        g = (r.get("symbol") or r.get("gene") or "").strip().upper()
        if g:
            cons[g] = {"d": r.get("direction", ""), "t": r.get("known_target", "").strip()}
    return ora, gsea, psum, dsum, cons

def build_pathway_indices():
    """pathways.js (full FDR<0.05 term index, loaded on pathways page only),
    gene_pathways.js (trimmed gene->terms, loaded on gene page only),
    gene_consensus.js (consensus membership + target, loaded on gene page only)."""
    ora, gsea, psum, dsum, cons = load_step8()
    terms = {}
    for r in ora:
        if not _fdr_ok(r["FDR"]):
            continue
        key = (r["database"], r["term_id"], r["term_name"])
        terms.setdefault(key, []).append(
            [r["contrast"], r["layer"], "ora_" + r["direction"], r["gene_ratio"], float(r["FDR"])])
    for r in gsea:
        if not _fdr_ok(r["FDR"]):
            continue
        key = (r["collection"], r["term_id"], r["term_name"])
        terms.setdefault(key, []).append(
            [r["contrast"], r["layer"], "gsea", float(r["NES"]), float(r["FDR"])])
    pw = {tid: {"n": nm, "d": db, "h": sorted(v, key=lambda x: x[4])}
          for (db, tid, nm), v in sorted(terms.items(), key=lambda kv: kv[0][2].lower())}
    with open(os.path.join(SITE, "pathways.js"), "w", encoding="utf-8") as fh:
        fh.write("const PATHWAYS = " + json.dumps(pw, ensure_ascii=False, separators=(",", ":")) + ";")
    # gene -> terms (only terms enriched in >=2 contrasts, top 12 per gene)
    from collections import Counter
    tcnt = Counter()
    for (db, tid, nm), v in terms.items():
        tcnt[(db, tid, nm)] = len(set(h[0] for h in v))
    keep = {k for k, c in tcnt.items() if c >= 2}
    g2t = {}
    for r in ora:
        if not _fdr_ok(r["FDR"]):
            continue
        k = (r["database"], r["term_id"], r["term_name"])
        if k not in keep:
            continue
        for g in r["genes"].split(";"):
            g = g.strip().upper()
            if g:
                g2t.setdefault(g, []).append(k)
    gpw = {}
    for g, tl in g2t.items():
        top = sorted(Counter(tl).items(), key=lambda x: -x[1])[:12]
        gpw[g] = [[t[2], t[0], t[1], n] for t, n in top]  # [name, db, id, n_contrasts]
    with open(os.path.join(SITE, "gene_pathways.js"), "w", encoding="utf-8") as fh:
        fh.write("const GENEPW = " + json.dumps(gpw, ensure_ascii=False, separators=(",", ":")) + ";")
    with open(os.path.join(SITE, "gene_consensus.js"), "w", encoding="utf-8") as fh:
        fh.write("const CONS = " + json.dumps(cons, ensure_ascii=False, separators=(",", ":")) + ";")
    print("pathway terms:", len(pw), "| genes w/ pathways:", len(gpw), "| consensus:", len(cons))

def _top_enrichment(cid, ora, gsea, n=4):
    """Top enriched terms for one cohort id: (up ORA, down ORA, top GSEA by |NES|)."""
    up = sorted([r for r in ora if r["layer"] == "bulk" and r["contrast"].startswith(cid + "_")
                 and r["direction"] == "up" and _fdr_ok(r["FDR"])],
                key=lambda r: float(r["FDR"]))[:n]
    dn = sorted([r for r in ora if r["layer"] == "bulk" and r["contrast"].startswith(cid + "_")
                 and r["direction"] == "down" and _fdr_ok(r["FDR"])],
                key=lambda r: float(r["FDR"]))[:n]
    gs = sorted([r for r in gsea if r["layer"] == "bulk" and r["contrast"].startswith(cid + "_")
                 and _fdr_ok(r["FDR"])],
                key=lambda r: -abs(float(r["NES"])))[:n]
    return up, dn, gs

# ---------------- site pages --------------------------------------------
CSS = """
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:1100px;margin:0 auto;padding:18px;color:#222;line-height:1.65;background:#fafafa}
h1{font-size:26px;border-bottom:2px solid #1a6fb5;padding-bottom:8px}
h2{font-size:20px;color:#1a6fb5;margin-top:34px}
h3{font-size:16px;margin-top:22px}
nav{background:#1a6fb5;padding:10px 18px;border-radius:8px;margin-bottom:18px}
nav a{color:#fff;margin-right:22px;text-decoration:none;font-weight:bold}
nav a:hover{text-decoration:underline}
.lang-toggle{float:right;font-weight:bold}
.lang-toggle a{margin:0 4px;opacity:.6}
.lang-toggle a.active{opacity:1;text-decoration:underline}
.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;margin:14px 0}
.stat{display:inline-block;background:#e8f1fa;border-radius:8px;padding:12px 18px;margin:6px 10px 6px 0;text-align:center}
.stat b{font-size:24px;display:block;color:#1a6fb5}
.caveat{background:#fff8e6;border-left:4px solid #e0a800;padding:8px 12px;margin:8px 0;font-size:14px}
.caveat b{color:#a87800}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}
th,td{border:1px solid #ddd;padding:6px 8px;text-align:left}
th{background:#eef4fa}
tr:hover{background:#f6fbff}
input[type=text]{font-size:18px;padding:8px 12px;width:340px;border:2px solid #1a6fb5;border-radius:6px}
button{font-size:16px;padding:8px 20px;background:#1a6fb5;color:#fff;border:none;border-radius:6px;cursor:pointer}
button:hover{background:#145a94}
.badge{display:inline-block;font-size:12px;padding:2px 8px;border-radius:10px;background:#e0ecf7;color:#1a6fb5;margin-right:6px}
.badge.sig{background:#d4edda;color:#1d6b2f}
.badge.nonsig{background:#f0f0f0;color:#666}
.badge.warn{background:#fff3cd;color:#856404}
.footer{margin-top:40px;padding-top:12px;border-top:1px solid #ccc;font-size:13px;color:#777}
canvas{max-width:100%;background:#fff;border:1px solid #ddd;border-radius:8px}
a{color:#1a6fb5}
.disc{background:#fdecea;border:1px solid #e6a19a;border-radius:8px;padding:12px 16px;margin:16px 0}
.disc b{color:#b3352b}
"""

NAV = (f'<nav><a href="index.html" {dk("nav_home")}>{en_of("nav_home")}</a>'
       f'<a href="gene.html" {dk("nav_gene")}>{en_of("nav_gene")}</a>'
       f'<a href="cohorts.html" {dk("nav_cohorts")}>{en_of("nav_cohorts")}</a>'
       f'<a href="treatment.html" {dk("nav_treatment")}>{en_of("nav_treatment")}</a>'
       f'<a href="downloads.html" {dk("nav_downloads")}>{en_of("nav_downloads")}</a>'
       f'<a href="pathways.html" {dk("nav_pathways")}>{en_of("nav_pathways")}</a>'
       f'<a href="methods.html" {dk("nav_methods")}>{en_of("nav_methods")}</a>'
       '<span class="lang-toggle"><a href="#" data-lang="en" onclick="pa_setLang(\'en\');return false;">EN</a>'
       ' | <a href="#" data-lang="zh" onclick="pa_setLang(\'zh\');return false;">\u4e2d\u6587</a></span></nav>')
WORKING_NAME = "PolypAtlas — CRSwNP Multi-omics Resource"
DISCLAIMER = f'<div class="disc" {dk("disc")}>{en_of("disc")}</div>'
FOOTER = (f'<div class="footer">{WORKING_NAME} <span {dk("foot_working")}>{en_of("foot_working")}</span> '
          f'· {VERSION} · <span {dk("foot_build")}>{en_of("foot_build")}</span> {BUILD_DATE} · '
          f'<span {dk("foot_src")}>{en_of("foot_src")}</span> · '
          f'<span {dk("foot_auth")}>{en_of("foot_auth")}</span></div>')

I18N_SCRIPT = """<script>
window.PA_I18N = __I18N_JSON__;
function pa_setLang(l){
  if(l!=='en'&&l!=='zh') l='en';
  try{ localStorage.setItem('pa_lang', l); }catch(e){}
  document.documentElement.lang = (l==='zh' ? 'zh-CN' : 'en');
  document.querySelectorAll('[data-i18n]').forEach(function(el){
    var d = window.PA_I18N[el.getAttribute('data-i18n')];
    if(d && d[l]!==undefined) el.innerHTML = d[l];
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(function(el){
    var d = window.PA_I18N[el.getAttribute('data-i18n-ph')];
    if(d && d[l]!==undefined) el.setAttribute('placeholder', d[l]);
  });
  document.querySelectorAll('.lang-toggle a').forEach(function(a){
    a.classList.toggle('active', a.getAttribute('data-lang')===l);
  });
  if(window.PA_langChanged) window.PA_langChanged(l);
}
document.addEventListener('DOMContentLoaded', function(){
  var l = 'en';
  try{ l = localStorage.getItem('pa_lang') || 'en'; }catch(e){}
  pa_setLang(l);
});
</script>"""

def page(title_key, body):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{en_of(title_key)} \u2014 {WORKING_NAME}</title>'
            f'<link rel="stylesheet" href="style.css"></head>\n'
            f'<body>{NAV}<h1>{WORKING_NAME}</h1>'
            f'<h2 {dk(title_key)}>{en_of(title_key)}</h2>{body}{FOOTER}'
            f'{I18N_SCRIPT.replace("__I18N_JSON__", i18n_json())}</body></html>')

def build_index():
    h = HEADLINE
    stats = "".join(
        f'<div class="stat"><b>{v}</b><span {dk(k)}>{en_of(k)}</span></div>'
        for k, v in [
            ("stat_series_curated", h["series_curated"]),
            ("stat_core", h["series_core"]),
            ("stat_samples", h["samples_curated"]),
            ("stat_bulk_cohorts", h["bulk_cohorts"]),
            ("stat_bulk_ev", f'{h["bulk_genes"]}×{h["bulk_cohorts"]}'),
            ("stat_sc_ds", h["sc_datasets"]),
            ("stat_sc_cells", h["sc_cells"]),
            ("stat_sc_donors", h["sc_donors"]),
            ("stat_sp_roi", h["spatial_roi"]),
            ("stat_sp_genes", h["spatial_genes"]),
            ("stat_endotype", h["endotype_series"]),
        ])
    body = (DISCLAIMER
        + f'<p {dk("idx_intro")}>{en_of("idx_intro")}</p>'
        + stats
        + f'<h3 {dk("idx_layers_h")}>{en_of("idx_layers_h")}</h3><ul>'
        + f'<li {dk("idx_bulk")}>{en_of("idx_bulk")}</li>'
        + f'<li {dk("idx_sc")}>{en_of("idx_sc")}</li>'
        + f'<li {dk("idx_sp")}>{en_of("idx_sp")}</li></ul>'
        + f'<h3 {dk("idx_start_h")}>{en_of("idx_start_h")}</h3><p {dk("idx_start")}>{en_of("idx_start")}</p>'
        + f'<div class="caveat" {dk("idx_honest")}>{en_of("idx_honest")}</div>')
    return page("title_home", body)

def build_gene():
    quick = " ".join(f'<button onclick="searchGene(\'{g}\')">{g}</button>' for g in QUICK_GENES)
    body = (DISCLAIMER
        + f'<div class="card"><input type="text" id="q" data-i18n-ph="gene_ph" placeholder="{en_of("gene_ph")}" onkeydown="if(event.key===\'Enter\')searchGene()">'
          f' <button onclick="searchGene()" {dk("gene_go")}>{en_of("gene_go")}</button></div>'
        + f'<p><span {dk("gene_quick")}>{en_of("gene_quick")}</span> {quick}</p><div id="result"></div>'
        + '<script src="data.js"></script>\n<script src="gene_pathways.js"></script>\n<script src="gene_consensus.js"></script>\n<script src="f1_meta.js"></script>\n<script src="f1_meta_cohorts.js"></script>\n<script src="f4_coexpr.js"></script>\n<script src="f3_genetic.js"></script>\n<script src="f6_lit.js"></script>\n<script src="gene_app.js"></script>')
    return page("title_gene", body)

def build_cohort_analysis():
    """Per-bulk-cohort analysis-layer cards: top enriched pathways, significant
    programs, deconvolution estimates, link to full DE tables."""
    ora, gsea, psum, dsum, _ = load_step8()
    cards = []
    for c in BULK_COHORTS:
        cid = c["id"]
        up, dn, gs = _top_enrichment(cid, ora, gsea)
        if up or dn or gs:
            parts = []
            if up:
                parts.append("<b>ORA up:</b> " + "; ".join(
                    f'{_html.escape(r["term_name"])} ({_html.escape(r["database"])}, FDR={float(r["FDR"]):.2g})' for r in up))
            if dn:
                parts.append("<b>ORA down:</b> " + "; ".join(
                    f'{_html.escape(r["term_name"])} ({_html.escape(r["database"])}, FDR={float(r["FDR"]):.2g})' for r in dn))
            if gs:
                parts.append("<b>GSEA:</b> " + "; ".join(
                    f'{_html.escape(r["term_name"])} (NES={float(r["NES"]):+.2f}, FDR={float(r["FDR"]):.2g})' for r in gs))
            enr = "<br>".join(parts)
        else:
            enr = f'<span style="color:#888" {dk("an_enr_ns")}>{en_of("an_enr_ns")}</span>'
        prows = [r for r in psum if r["cohort"] == cid and _fdr_ok(r["FDR"])]
        up_p = [r["program"] for r in prows if float(r["diff"]) > 0]
        dn_p = [r["program"] for r in prows if float(r["diff"]) < 0]
        if prows:
            prog = (f'<b {dk("an_prog_up")}>{en_of("an_prog_up")}</b>: {", ".join(up_p) or "—"}<br>'
                    f'<b {dk("an_prog_down")}>{en_of("an_prog_down")}</b>: {", ".join(dn_p) or "—"}')
        else:
            prog = f'<span style="color:#888" {dk("an_prog_ns")}>{en_of("an_prog_ns")}</span>'
        drows = [r for r in dsum if r["cohort"] == cid and _fdr_ok(r["FDR"])]
        if drows:
            dec = (", ".join(f'{r["population"]} {"▲" if float(r["diff"]) > 0 else "▼"}' for r in drows)
                   + f'<br><span style="font-size:12px;color:#666" {dk("an_deconv_lab")}>{en_of("an_deconv_lab")}</span>')
        else:
            dec = (f'<span style="color:#888" {dk("an_deconv_ns")}>{en_of("an_deconv_ns")}</span>'
                   f'<br><span style="font-size:12px;color:#666" {dk("an_deconv_lab")}>{en_of("an_deconv_lab")}</span>')
        cards.append(
            f'<div class="card"><h3>{cid}</h3>'
            f'<p><b {dk("an_enr")}>{en_of("an_enr")}</b><br><span style="font-size:13px">{enr}</span></p>'
            f'<p><b {dk("an_prog")}>{en_of("an_prog")}</b><br><span style="font-size:13px">{prog}</span></p>'
            f'<p><b {dk("an_deconv")}>{en_of("an_deconv")}</b><br><span style="font-size:13px">{dec}</span></p>'
            f'<p style="font-size:13px"><a href="data/de_tables.zip" {dk("an_det")}>{en_of("an_det")}</a></p></div>')
    return (f'<h2 {dk("an_h")}>{en_of("an_h")}</h2>' + "".join(cards))

def build_cohorts():
    rows = []
    for c in BULK_COHORTS:
        tag = (f'<div class="caveat" {dk("cav_" + c["id"])}>{en_of("cav_" + c["id"])}</div>'
               if c.get("caveat") else "")
        note = (f'<br><span style="font-size:13px;color:#555" {dk("note_" + c["id"])}>{en_of("note_" + c["id"])}</span>'
                if c.get("note") else "")
        rows.append(f'<tr><td><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={c["id"].split("_")[0]}">{c["id"]}</a></td>'
                    f'<td {dk("n_" + c["id"])}>{c["n_en"]}</td><td>{c["method"]}</td><td>{c["sig"]}</td>'
                    f'<td>{note}{tag}</td></tr>')
    bulk_tbl = (f'<h3 {dk("co_bulk_h")}>{en_of("co_bulk_h")}</h3>'
                f'<table><tr><th {dk("co_th_id")}>{en_of("co_th_id")}</th>'
                f'<th {dk("co_th_contrast")}>{en_of("co_th_contrast")}</th>'
                f'<th {dk("co_th_method")}>{en_of("co_th_method")}</th>'
                f'<th {dk("co_th_sig")}>{en_of("co_th_sig")}</th>'
                f'<th {dk("co_th_note")}>{en_of("co_th_note")}</th></tr>'
                + "".join(rows) + "</table>")
    sc_rows = []
    for d in SC_DATASETS:
        tag = (f'<div class="caveat" {dk("sc_cav_" + d["id"])}>{en_of("sc_cav_" + d["id"])}</div>'
               if d.get("caveat") else "")
        note = (f'<br><span style="font-size:13px;color:#555" {dk("sc_note_" + d["id"])}>{en_of("sc_note_" + d["id"])}</span>'
                if d.get("note") else "")
        donors_td = (f'<td {dk("sc_donors_" + d["id"])}>{d["donors_en"]}</td>' if "donors_en" in d
                     else f'<td>{d["donors"]}</td>')
        sc_rows.append(f'<tr><td><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={d["id"]}">{d["id"]}</a></td>'
                       f'<td>{d["cells"]}</td>'
                       + donors_td +
                       f'<td {dk("sc_design_" + d["id"])}>{d["design_en"]}</td>'
                       f'<td>{note}{tag}</td></tr>')
    sc_tbl = (f'<h3 {dk("co_sc_h")}>{en_of("co_sc_h")}</h3>'
              f'<p {dk("co_sc_intro")}>{en_of("co_sc_intro")}</p>'
              f'<table><tr><th {dk("co_th_id")}>{en_of("co_th_id")}</th>'
              f'<th {dk("co_th_cells")}>{en_of("co_th_cells")}</th>'
              f'<th {dk("co_th_donors")}>{en_of("co_th_donors")}</th>'
              f'<th {dk("co_th_design")}>{en_of("co_th_design")}</th>'
              f'<th {dk("co_th_note")}>{en_of("co_th_note")}</th></tr>'
              + "".join(sc_rows) + "</table>")
    sp = SPATIAL_INFO
    sp_sec = (f'<h3 {dk("co_sp_h")}>{en_of("co_sp_h")}</h3>'
              f'<p><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={sp["id"]}">{sp["id"]}</a> '
              f'<span {dk("co_sp_intro")}>{en_of("co_sp_intro")}</span></p>'
              + "".join(f'<div class="caveat" {dk(f"sp_cav_{i}")}>{en_of(f"sp_cav_{i}")}</div>'
                        for i in range(len(sp["caveats"]))))
    other = (f'<h3 {dk("co_other_h")}>{en_of("co_other_h")}</h3><ul>'
             + "".join(f'<li {dk(f"co_o{i}")}>{en_of(f"co_o{i}")}</li>' for i in (1, 2, 3))
             + "</ul>")
    body = DISCLAIMER + bulk_tbl + build_cohort_analysis() + sc_tbl + sp_sec + other
    return page("title_cohorts", body)

PATH_APP_JS = r"""
function p_lang(){ try{ return localStorage.getItem('pa_lang')||'en'; }catch(e){ return 'en'; } }
function p_t(k){ var l=p_lang(); var d=window.PA_I18N[k]; return d?d[l]:k; }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtf(v){ if(v==0) return '0'; if(v<1e-3) return v.toExponential(1); return v.toFixed(4); }
function searchPath(){
  var q=(document.getElementById('pq').value||'').trim().toLowerCase();
  var box=document.getElementById('presult');
  var btn=document.getElementById('pgo');
  if(!q){ box.innerHTML='<p>'+p_t('path_none')+'</p>'; return; }
  var all=Object.entries(PATHWAYS).filter(function(e){ return e[1].n.toLowerCase().indexOf(q)>=0; });
  if(!all.length){ box.innerHTML='<p>'+p_t('path_none')+'</p>'; return; }
  var shown=all.slice(0,100);
  var h='<table><tr><th>'+p_t('path_th_term')+'</th><th>'+p_t('path_th_db')+'</th><th>'+p_t('path_th_ev')+'</th><th>'+p_t('path_th_stat')+'</th></tr>';
  shown.forEach(function(e){
    var id=e[0], t=e[1];
    var ev=t.h.map(function(x){
      var badge = x[2]==='gsea' ? 'GSEA' : x[2];
      return esc(x[0])+' <span class="badge">'+badge+'</span>';
    }).join('<br>');
    var st=t.h.map(function(x){
      var m = x[2]==='gsea' ? ('NES '+(+x[3]).toFixed(2)) : ('ratio '+x[3]);
      return m+'<br><span style="color:#666">FDR='+fmtf(x[4])+'</span>';
    }).join('<br>');
    h+='<tr><td><b>'+esc(t.n)+'</b><br><span style="font-size:12px;color:#666">'+esc(id)+'</span></td>'
      +'<td>'+esc(t.d)+'</td><td style="font-size:12px">'+ev+'</td><td style="font-size:12px">'+st+'</td></tr>';
  });
  h+='</table>';
  if(all.length>100) h+='<p style="color:#888">'+p_t('path_more')+' ('+all.length+' hits)</p>';
  box.innerHTML=h;
}
"""

def build_pathways():
    body = (DISCLAIMER
        + f'<p {dk("path_intro")}>{en_of("path_intro")}</p>'
        + f'<div class="caveat" {dk("path_note")}>{en_of("path_note")}</div>'
        + f'<div class="card"><input type="text" id="pq" data-i18n-ph="path_ph" placeholder="{en_of("path_ph")}" onkeydown="if(event.key===\'Enter\')searchPath()">'
          f' <button id="pgo" onclick="searchPath()" {dk("path_go")}>{en_of("path_go")}</button></div>'
        + '<div id="presult"></div>'
        + '<script src="pathways.js"></script>\n<script>\n' + PATH_APP_JS + '\n</script>')
    return page("title_pathways", body)

def build_treatment():
    s9 = os.path.join(PROJ, "analysis", "step9_features")
    t10 = json.load(open(os.path.join(s9, "f10_treatment.json")))
    co = t10["cohorts"][0]
    st = co["stats"]
    # marker reversal table
    mrows = "".join(
        f"<tr><td>{m['gene']}</td><td>{m['logFC']:.3f}</td><td>{m['FDR']:.4g}</td>"
        f"<td>{'&#10003;' if m['direction_correct'] else '&#10007;'}</td>"
        f"<td>{'&#10003;' if m['significant_FDR05'] else ''}</td></tr>"
        for m in t10["marker_reversal"])
    marker_tbl = ("<table><tr><th>Gene</th><th>logFC (post vs pre)</th><th>FDR</th>"
                  "<th>Direction correct</th><th>FDR&lt;0.05</th></tr>" + mrows + "</table>")
    # program changes table (bold FDR<0.05)
    prows = "".join(
        f"<tr{' style=\"font-weight:bold\"' if p['FDR'] < 0.05 else ''}>"
        f"<td>{p['program']}</td><td>{p['delta_post_minus_pre']:.4f}</td>"
        f"<td>{p['FDR']:.3g}</td><td>{p['n_pairs']}</td></tr>"
        for p in t10["program_scores_changes"])
    prog_tbl = ("<table><tr><th>Program</th><th>&Delta; (post &minus; pre)</th><th>FDR</th>"
                "<th>Pairs</th></tr>" + prows + "</table>")
    # inventory
    inv = t10["treatment_contrasts_inventory"]["clinical_treatment"]
    irows = "".join(
        f"<tr><td>{c['gse']}</td><td>{c['contrast']}</td><td>{c['n_case']}/{c['n_control']}</td>"
        f"<td>{c['method']}</td><td>{c['note']}</td></tr>" for c in inv)
    inv_tbl = ("<table><tr><th>Series</th><th>Contrast</th><th>n (treat/ctrl)</th>"
               "<th>Method</th><th>Note</th></tr>" + irows + "</table>")
    # drug reversal table (top 50, in-silico only)
    drugs = []
    with open(os.path.join(s9, "f2_drugs.csv")) as fh:
        for row in csv.DictReader(fh):
            drugs.append(row)
    drows = "".join(
        f"<tr><td>{d['rank']}</td><td>{d['compound']}</td><td>{d['cell_line']}</td>"
        f"<td>{d['dose']} {d['dose_unit']}</td><td>{float(d['score']):.4f}</td></tr>"
        for d in drugs)
    drug_tbl = ("<table><tr><th>#</th><th>Compound</th><th>Cell line</th><th>Dose</th>"
                "<th>Overlap score</th></tr>" + drows + "</table>")
    body = (DISCLAIMER
        + f"<p {dk('t_intro')}>{en_of('t_intro')}</p>"
        + f"<div class=\"caveat\" {dk('t_cav')}>{en_of('t_cav')}</div>"
        + f"<h3 {dk('t_dup_h')}>{en_of('t_dup_h')}</h3>"
        + f"<p>{co['design']}</p>"
        + f"<p><b><span {dk('t_dup_stats')}>{en_of('t_dup_stats')}</span>:</b> "
        f"dupilumab {st['dupilumab_DE_FDR05']} / placebo {st['placebo_DE_FDR05']} "
        f"(paired; Early Termination excluded)</p>"
        + f'<p><img src="f10_dupilumab_paired_scores.png" style="max-width:100%"></p>'
        + f"<h3 {dk('t_marker_h')}>{en_of('t_marker_h')}</h3>" + marker_tbl
        + f"<p {dk('t_marker_note')}>{en_of('t_marker_note')}</p>"
        + f"<h3 {dk('t_prog_h')}>{en_of('t_prog_h')}</h3>" + prog_tbl
        + f"<p {dk('t_prog_note')}>{en_of('t_prog_note')}</p>"
        + f"<h3 {dk('t_inv_h')}>{en_of('t_inv_h')}</h3>" + inv_tbl
        + f"<p {dk('t_inv_note')}>{en_of('t_inv_note')}</p>"
        + f"<h3 {dk('t_drug_h')}>{en_of('t_drug_h')}</h3>"
        + f"<p {dk('t_drug_method')}>{en_of('t_drug_method')}</p>" + drug_tbl)
    return page("title_treatment", body)

def build_downloads():
    items = [
        ("evidence_matrix_logFC.csv", "dl_evlfc"),
        ("evidence_matrix_FDR.csv", "dl_evfdr"),
        ("de_tables.zip", "dl_dezip"),
        ("runlog.csv", "dl_runlog"),
        ("controls_panel.csv", "dl_panel"),
        ("celltype_evidence_matrix.csv", "dl_scev"),
        ("composition_all.csv", "dl_comp"),
        ("alignment_table.csv", "dl_align"),
        ("roi_metadata.csv", "dl_roi"),
        ("curation_table.csv", "dl_cur"),
        ("enrichment_ora.csv", "dl8_ora"),
        ("enrichment_gsea.csv", "dl8_gsea"),
        ("program_scores.csv", "dl8_psc"),
        ("program_summary.csv", "dl8_psm"),
        ("deconv_scores.csv", "dl8_dsc"),
        ("deconv_summary.csv", "dl8_dsm"),
        ("consensus_annotated.csv", "dl8_can"),
        ("consensus_enrichment.csv", "dl8_cen"),
        ("lr_interactions_CRSwNP_vs_control.csv", "dl8_lr1"),
        ("lr_interactions_CRSsNP_vs_control.csv", "dl8_lr2"),
        ("meta_combined.csv", "dl9_f1meta"),
        ("meta_percohort.csv", "dl9_f1coh"),
        ("drug_reversal_l1000cds2.csv", "dl9_f2"),
        ("genetic_support.csv", "dl9_f3"),
        ("coexpression_top10.csv", "dl9_f4"),
        ("literature_support.csv", "dl9_f6"),
        ("treatment_response.json", "dl9_f10"),
    ]
    # v1.3 download-label keys live in _dl9; register them as _STRINGS entries
    for k, en, zh in _dl9:
        if k not in _STRINGS:
            _STRINGS[k] = (en, zh)
    lis = "".join(f'<li><a href="data/{f}">{f}</a> — <span {dk(k)}>{en_of(k)}</span></li>' for f, k in items)
    body = (DISCLAIMER + "<ul>" + lis + "</ul>"
            + f'<div class="caveat" {dk("dl_usage")}>{en_of("dl_usage")}</div>')
    return page("title_downloads", body)

def build_methods():
    lis = "".join(f'<li {dk(f"m_f{i}")}>{en_of(f"m_f{i}")}</li>' for i in range(1, 7))
    lims = "".join(f'<li {dk(f"m_l{i}")}>{en_of(f"m_l{i}")}</li>' for i in range(1, 9))
    body = (DISCLAIMER
        + f'<h3 {dk("m_flow_h")}>{en_of("m_flow_h")}</h3><ol>' + lis + "</ol>"
        + f'<h3 {dk("m_lim_h")}>{en_of("m_lim_h")}</h3><ul>' + lims + "</ul>"
        + f'<h3 {dk("m_src_h")}>{en_of("m_src_h")}</h3><p {dk("m_src")}>{en_of("m_src")}</p>'
        + f'<h3 {dk("m_auth_h")}>{en_of("m_auth_h")}</h3><p {dk("m_auth")}>{en_of("m_auth")}</p>')
    return page("title_methods", body)

# ---- gene_app.js: JS-side strings are keys into the same embedded dictionary ----
# JS needs its own literals (no JSON fetch), so build a JS object from the g_* keys.
def gene_js_strings():
    keys = ["g_empty", "g_notfound", "g_suggest", "g_nosim", "g_bulk_t", "g_th_cohort",
            "g_th_contrast", "g_th_comp", "g_th_desc", "g_limit_badge", "g_bulk_chart",
            "g_sc_t", "g_bulk_nm", "g_sc_nm", "g_sp_t", "g_cd45", "g_panck",
            "g_sp_cav", "g_notpanel", "g_lim_colon",
            "gpw_t", "gpw_path", "gpw_cons", "gpw_cons_up", "gpw_cons_down",
            "gpw_cons_no", "gpw_target", "gpw_ncol", "path_th_term", "path_th_db",
            "g_f1_t", "g_f1_combined", "g_f1_ci", "g_f1_p", "g_f1_i2", "g_f1_k",
            "g_f1_method", "g_f1_forest",
            "g_f4_t", "g_f4_method", "g_f4_th_g", "g_f4_th_r", "g_f4_th_k",
            "g_f3_t", "g_f3_gwas", "g_f3_trait", "g_f3_bestp", "g_f3_n",
            "g_f3_eqtl", "g_f3_proxy", "g_f3_method",
            "g_f6_t", "g_f6_method", "g_f6_claims", "g_f6_rep", "g_f6_dir", "g_f6_not"]
    obj = {k: {"en": en_of(k), "zh": zh_of(k)} for k in keys}
    # caveat full blocks keyed cav_<id> for the dynamic gene page
    cav = {k: {"en": en_of(k), "zh": zh_of(k)} for k in _STRINGS
           if k.startswith("cav_")}
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")), json.dumps(cav, ensure_ascii=False, separators=(",", ":"))

GENE_APP_JS_TEMPLATE = r"""
const BULK = DATA.coho, SCN = DATA.scl, GENES = DATA.genes;
const GS = __GS_JSON__, CAV = __CAV_JSON__;
function pa_lang(){ try{ return localStorage.getItem('pa_lang') || 'en'; }catch(e){ return 'en'; } }
function gs(k){ const l = pa_lang(); const d = GS[k]; return d ? (d[l]!==undefined ? d[l] : d.en) : k; }
function cavtxt(id){ const l = pa_lang(); const d = CAV['cav_'+id]; return d ? d[l] : ''; }
function fmt(v, d){ if(v==null) return '<span style="color:#aaa">—</span>'; return Number(v).toFixed(d); }
function badge(f){ if(f==null) return ''; if(f<0.05) return '<span class="badge sig">FDR<0.05</span>'; return '<span class="badge nonsig">ns</span>'; }
function searchGene(g0){
  let q = (g0 || document.getElementById('q').value || '').trim().toUpperCase();
  const box = document.getElementById('result');
  if(!q){ box.innerHTML = '<p>'+gs('g_empty')+'</p>'; window._lastGene = null; return; }
  let key = Object.keys(GENES).find(k => k.toUpperCase() === q);
  if(!key){ // prefix suggestions
    let cand = Object.keys(GENES).filter(k => k.toUpperCase().startsWith(q)).slice(0,20);
    box.innerHTML = '<p>'+gs('g_notfound')+' <b>'+q+'</b>.' + (cand.length? ' '+gs('g_suggest')+' '+cand.map(c=>`<a href="#" onclick="searchGene('${c}');return false;">${c}</a>`).join('、') : ' '+gs('g_nosim')) + '</p>';
    window._lastGene = null; return;
  }
  window._lastGene = key;
  document.getElementById('q').value = key;
  const r = GENES[key];
  let html = '<div class="card"><h3>'+key+'</h3>';
  // bulk table + chart
  html += '<h3>'+gs('g_bulk_t')+'</h3><table><tr><th>'+gs('g_th_cohort')+'</th><th>logFC</th><th>FDR</th><th></th></tr>';
  const vals = [];
  if(r.b){
    BULK.forEach((c,i)=>{
      const e = r.b[i]; vals.push(e?e[0]:null);
      const ntxt = c['n_'+pa_lang()] || c.n_en || c.n_zh;
      html += '<tr><td>'+c.id+'<br><span style="font-size:12px;color:#666">'+ntxt+'</span>'
        + (c.caveat? '<br><span class="badge warn">'+gs('g_limit_badge')+'</span>' : '') + '</td>'
        + '<td>'+fmt(e?e[0]:null,3)+'</td><td>'+fmt(e?e[1]:null,4)+'</td><td>'+badge(e?e[1]:null)+'</td></tr>';
    });
  } else html += '<tr><td colspan="4">'+gs('g_bulk_nm')+'</td></tr>';
  html += '</table>';
  const caveats = BULK.filter(c=>c.caveat && r.b && BULK.indexOf(c)<r.b.length && r.b[BULK.indexOf(c)]);
  const shown = [...new Set(caveats.map(c=>'<div class="caveat">'+cavtxt(c.id)+'</div>'))];
  if(shown.length) html += shown.join('');
  html += '<h3>'+gs('g_bulk_chart')+'</h3><canvas id="cv" width="900" height="340"></canvas></div>';
  // pathways & consensus block
  html += '<div class="card"><h3>'+gs('gpw_t')+'</h3>';
  const pw = (typeof GENEPW!=='undefined') ? GENEPW[key] : null;
  if(pw && pw.length){
    html += '<p><b>'+gs('gpw_path')+'</b></p><table><tr><th>'+gs('path_th_term')+'</th><th>'+gs('path_th_db')+'</th><th>'+gs('gpw_ncol')+'</th></tr>';
    pw.forEach(function(p){ html += '<tr><td>'+p[0]+'</td><td>'+p[1]+'</td><td>'+p[3]+'</td></tr>'; });
    html += '</table>';
  } else html += '<p style="color:#888">—</p>';
  const cs = (typeof CONS!=='undefined') ? CONS[key] : null;
  html += '<p><b>'+gs('gpw_cons')+':</b> ';
  if(cs){ html += (cs.d==='up' ? gs('gpw_cons_up') : gs('gpw_cons_down'));
    if(cs.t) html += ' · <span class="badge sig">'+gs('gpw_target')+': '+cs.t+'</span>';
  } else html += gs('gpw_cons_no');
  html += '</p></div>';
  // v1.3 added-value layers (F1/F4/F3/F6): render only when data exist for the gene
  html += f1Block(key) + f4Block(key) + f3Block(key) + f6Block(key);
  // sc table
  html += '<div class="card"><h3>'+gs('g_sc_t')+'</h3>';
  if(r.s){
    html += '<table><tr><th>'+gs('g_th_contrast')+'</th><th>logFC</th><th>FDR</th><th></th></tr>';
    Object.keys(r.s).forEach(i=>{
      const e = r.s[i];
      html += '<tr><td>'+SCN[+i]+'</td><td>'+fmt(e[0],3)+'</td><td>'+fmt(e[1],4)+'</td><td>'+badge(e[1])+'</td></tr>';
    });
    html += '</table>';
  } else html += '<p>'+gs('g_sc_nm')+'</p>';
  html += '</div>';
  // spatial
  html += '<div class="card"><h3>'+gs('g_sp_t')+'</h3>';
  if(r.sp){
    html += '<table><tr><th>'+gs('g_th_comp')+'</th><th>'+gs('g_th_desc')+'</th><th>FDR</th></tr>'
      + '<tr><td>'+gs('g_cd45')+'</td><td>'+fmt(r.sp[0],3)+'</td><td>'+fmt(r.sp[1],4)+'</td></tr>'
      + '<tr><td>'+gs('g_panck')+'</td><td>'+fmt(r.sp[2],3)+'</td><td>'+fmt(r.sp[3],4)+'</td></tr></table>'
      + '<div class="caveat">'+gs('g_sp_cav')+'</div>';
  } else html += '<p>'+gs('g_notpanel')+'</p>';
  html += '</div>';
  box.innerHTML = html;
  drawChart(vals);
  drawF1Forest(key);
}
// ---- v1.3: added-value layers (F1 cross-cohort meta, F4 co-expression, F3 genetic, F6 literature) ----
function fmtP(p){ if(p==null) return '<span style="color:#aaa">—</span>'; if(p<1e-4) return Number(p).toExponential(1); return Number(p).toFixed(4); }
function f1Block(key){
  const m = (typeof F1META!=='undefined') ? F1META[key] : null;
  if(!m) return '';
  let html = '<div class="card"><h3>'+gs('g_f1_t')+'</h3>';
  html += '<p><b>'+gs('g_f1_combined')+':</b> '+fmt(m.lfc,3)+' &nbsp; <b>'+gs('g_f1_ci')+':</b> ['+fmt(m.lo,3)+', '+fmt(m.hi,3)+'] &nbsp; <b>'+gs('g_f1_p')+':</b> '+fmtP(m.p)+' &nbsp; <b>'+gs('g_f1_i2')+':</b> '+fmt(m.i2,1)+'% &nbsp; <b>'+gs('g_f1_k')+':</b> '+m.k+'</p>';
  html += '<h4>'+gs('g_f1_forest')+'</h4><canvas id="cv_f1" width="900" height="360"></canvas>';
  html += '<p style="font-size:12px;color:#666">'+gs('g_f1_method')+'</p></div>';
  return html;
}
function drawF1Forest(key){
  const cv = document.getElementById('cv_f1'); if(!cv) return;
  const rows = (typeof F1COHORTS!=='undefined' && typeof F1COHORT_ORDER!=='undefined') ? F1COHORTS[key] : null;
  const m = (typeof F1META!=='undefined') ? F1META[key] : null;
  if(!rows || !m) return;
  const ctx = cv.getContext('2d');
  const present = F1COHORT_ORDER.map(function(c,i){ return {c:c, v:rows[i]}; }).filter(function(x){ return x.v; });
  const n = present.length; if(!n) return;
  cv.height = 60 + n*26 + 64;
  const W = cv.width, H = cv.height;
  const all = [];
  present.forEach(function(x){ all.push(x.v[0]-1.96*x.v[1], x.v[0]+1.96*x.v[1]); });
  all.push(m.lo, m.hi, 0);
  let mn = Math.min.apply(null, all), mx = Math.max.apply(null, all);
  const pad = (mx-mn)*0.1 || 0.5; mn -= pad; mx += pad;
  const X = function(v){ return 190 + (v-mn)/(mx-mn)*(W-210); };
  const rowY = function(i){ return 44 + i*26; };
  ctx.clearRect(0,0,W,H);
  ctx.font = '12px sans-serif';
  ctx.strokeStyle = '#999'; ctx.beginPath(); ctx.moveTo(X(0),24); ctx.lineTo(X(0),H-44); ctx.stroke();
  present.forEach(function(x,i){
    const y = rowY(i), lfc = x.v[0], se = x.v[1];
    ctx.fillStyle = '#333'; ctx.fillText(x.c, 8, y+4);
    ctx.strokeStyle = '#5a8fd4'; ctx.beginPath(); ctx.moveTo(X(lfc-1.96*se),y); ctx.lineTo(X(lfc+1.96*se),y); ctx.stroke();
    ctx.fillStyle = '#1f5fa8'; ctx.fillRect(X(lfc)-4, y-4, 8, 8);
    ctx.fillStyle = '#666'; ctx.fillText(lfc.toFixed(2), W-64, y+4);
  });
  const dy = 44 + n*26 + 22;
  ctx.fillStyle = '#333'; ctx.fillText('META (RE)', 8, dy+4);
  ctx.fillStyle = '#b33';
  ctx.beginPath();
  ctx.moveTo(X(m.lo),dy); ctx.lineTo(X(m.lfc),dy-9); ctx.lineTo(X(m.hi),dy); ctx.lineTo(X(m.lfc),dy+9);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#666'; ctx.fillText(m.lfc.toFixed(2)+' ['+m.lo.toFixed(2)+', '+m.hi.toFixed(2)+']', W-64, dy+4);
}
function f4Block(key){
  const rows = (typeof F4COEXPR!=='undefined') ? F4COEXPR[key] : null;
  if(!rows || !rows.length) return '';
  let html = '<div class="card"><h3>'+gs('g_f4_t')+'</h3><table><tr><th>'+gs('g_f4_th_g')+'</th><th>'+gs('g_f4_th_r')+'</th><th>'+gs('g_f4_th_k')+'</th></tr>';
  rows.forEach(function(r){
    html += '<tr><td><a href="#" onclick="searchGene(\''+r[0]+'\');return false;">'+r[0]+'</a></td><td>'+r[1].toFixed(3)+'</td><td>'+r[2]+'</td></tr>';
  });
  html += '</table><p style="font-size:12px;color:#666">'+gs('g_f4_method')+'</p></div>';
  return html;
}
function f3Block(key){
  const rows = (typeof F3GENETIC!=='undefined') ? F3GENETIC[key] : null;
  if(!rows || !rows.length) return '';
  const gwas = rows.filter(function(r){ return r.source==='GwasCatalog'; });
  const eqtl = rows.filter(function(r){ return r.source==='GTEx'; });
  let html = '<div class="card"><h3>'+gs('g_f3_t')+'</h3>';
  if(gwas.length){
    html += '<p><b>'+gs('g_f3_gwas')+'</b></p><table><tr><th>'+gs('g_f3_trait')+'</th><th>'+gs('g_f3_bestp')+'</th></tr>';
    gwas.forEach(function(r){ html += '<tr><td>'+r.trait+'</td><td>'+fmtP(r.bestp)+'</td></tr>'; });
    html += '</table>';
  }
  if(eqtl.length){
    html += '<p><b>'+gs('g_f3_eqtl')+':</b> '+eqtl.map(function(r){ return r.trait; }).join(' \u00b7 ')+'</p>';
    html += '<div class="caveat">'+gs('g_f3_proxy')+'</div>';
  }
  html += '<p style="font-size:12px;color:#666">'+gs('g_f3_method')+'</p></div>';
  return html;
}
function f6Block(key){
  const r = (typeof F6LIT!=='undefined') ? F6LIT[key] : null;
  if(!r) return '';
  let html = '<div class="card"><h3>'+gs('g_f6_t')+'</h3>';
  html += '<p><b>'+r.t+'</b> '+gs('g_f6_claims')+': <span class="badge sig">'+r.r+' '+gs('g_f6_rep')+'</span> <span class="badge">'+r.d+' '+gs('g_f6_dir')+'</span>'
    + (r.n ? ' <span class="badge warn">'+r.n+' '+gs('g_f6_not')+'</span>' : '') + '</p>';
  html += '<p style="font-size:12px;color:#666">'+gs('g_f6_method')+'</p></div>';
  return html;
}
function drawChart(vals){
  const cv = document.getElementById('cv'); if(!cv) return;
  const ctx = cv.getContext('2d');
  const W = cv.width, H = cv.height;
  const maxA = Math.max(0.5, ...vals.filter(v=>v!=null).map(Math.abs));
  const bw = W / BULK.length;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle = '#666'; ctx.font = '11px sans-serif';
  const zero = H/2;
  ctx.strokeStyle = '#999'; ctx.beginPath(); ctx.moveTo(0,zero); ctx.lineTo(W,zero); ctx.stroke();
  BULK.forEach((c,i)=>{
    const v = vals[i]; if(v==null) return;
    const h = (v/maxA)*(H/2-24);
    ctx.fillStyle = v>0 ? '#d45a5a' : '#5a8fd4';
    ctx.fillRect(i*bw+4, v>0? zero-h : zero, bw-8, Math.abs(h));
    ctx.save(); ctx.translate(i*bw+bw/2, H-4); ctx.rotate(-0.5);
    ctx.fillStyle='#333'; ctx.fillText(c.id.split('_')[0], 0, 0); ctx.restore();
  });
}
document.getElementById('q').addEventListener('keydown', e=>{ if(e.key==='Enter') searchGene(); });
// re-render results when the page language changes (wired from the inline i18n script)
window.PA_langChanged = function(){ if(window._lastGene) searchGene(window._lastGene); };
"""

def zh_of(key):
    return _STRINGS[key][1]

# ---------------- main ----------------------------------------------------
def main():
    os.makedirs(SITE, exist_ok=True)
    data_dir = os.path.join(SITE, "data")
    os.makedirs(data_dir, exist_ok=True)

    genes, sc_labels, n_genes = build_gene_data()
    print(f"genes in union: {n_genes}")
    build_pathway_indices()

    data_js = {
        "version": VERSION, "build_date": BUILD_DATE,
        "coho": [{"id": c["id"], "n_en": c["n_en"], "n_zh": c["n"],
                  "caveat": bool(c.get("caveat"))} for c in BULK_COHORTS],
        "scl": sc_labels, "genes": genes,
    }
    js_text = "const DATA = " + json.dumps(data_js, separators=(",", ":"), ensure_ascii=False) + ";"
    with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as fh:
        fh.write(js_text)
    print("data.js bytes:", len(js_text.encode("utf-8")))

    with open(os.path.join(SITE, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    gs_json, cav_json = gene_js_strings()
    gene_app = (GENE_APP_JS_TEMPLATE
                .replace("__GS_JSON__", gs_json)
                .replace("__CAV_JSON__", cav_json))
    with open(os.path.join(SITE, "gene_app.js"), "w", encoding="utf-8") as fh:
        fh.write(gene_app)

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(build_index())
    with open(os.path.join(SITE, "gene.html"), "w", encoding="utf-8") as fh:
        fh.write(build_gene())
    with open(os.path.join(SITE, "cohorts.html"), "w", encoding="utf-8") as fh:
        fh.write(build_cohorts())
    with open(os.path.join(SITE, "downloads.html"), "w", encoding="utf-8") as fh:
        fh.write(build_downloads())
    with open(os.path.join(SITE, "pathways.html"), "w", encoding="utf-8") as fh:
        fh.write(build_pathways())
    with open(os.path.join(SITE, "treatment.html"), "w", encoding="utf-8") as fh:
        fh.write(build_treatment())
    with open(os.path.join(SITE, "methods.html"), "w", encoding="utf-8") as fh:
        fh.write(build_methods())

    # v1.3 feature JS indexes (gene page) + treatment figure
    s9 = os.path.join(PROJ, "analysis", "step9_features")
    for jsf in ["f1_meta.js", "f1_meta_cohorts.js", "f4_coexpr.js", "f3_genetic.js", "f6_lit.js"]:
        shutil.copy(os.path.join(s9, jsf), os.path.join(SITE, jsf))
    shutil.copy(os.path.join(s9, "f10_dupilumab_paired_scores.png"), os.path.join(SITE, "f10_dupilumab_paired_scores.png"))

    # v1.3 download files
    for src, dst in [
        (os.path.join(s9, "f1_meta.csv"), "meta_combined.csv"),
        (os.path.join(s9, "f1_meta_cohorts.csv"), "meta_percohort.csv"),
        (os.path.join(s9, "f2_drugs.csv"), "drug_reversal_l1000cds2.csv"),
        (os.path.join(s9, "f3_genetic.csv"), "genetic_support.csv"),
        (os.path.join(s9, "f4_coexpr.csv"), "coexpression_top10.csv"),
        (os.path.join(s9, "f6_lit.csv"), "literature_support.csv"),
        (os.path.join(s9, "f10_treatment.json"), "treatment_response.json"),
    ]:
        shutil.copy(src, os.path.join(data_dir, dst))

    # data copies for downloads page
    s2 = os.path.join(PROJ, "analysis", "step2_bulk")
    s3 = os.path.join(PROJ, "analysis", "step3_scrna")
    s4 = os.path.join(PROJ, "analysis", "step4_spatial")
    copies = [
        (os.path.join(s2, "evidence_matrix_logFC.csv"), "evidence_matrix_logFC.csv"),
        (os.path.join(s2, "evidence_matrix_FDR.csv"), "evidence_matrix_FDR.csv"),
        (os.path.join(s2, "runlog.csv"), "runlog.csv"),
        (os.path.join(s2, "controls_panel.csv"), "controls_panel.csv"),
        (os.path.join(s3, "celltype_evidence_matrix.csv"), "celltype_evidence_matrix.csv"),
        (os.path.join(s3, "composition_all.csv"), "composition_all.csv"),
        (os.path.join(s4, "alignment_table.csv"), "alignment_table.csv"),
        (os.path.join(s4, "roi_metadata.csv"), "roi_metadata.csv"),
        (os.path.join(PROJ, "curation", "curation_table.csv"), "curation_table.csv"),
    ]
    for src, dst in copies:
        shutil.copy(src, os.path.join(data_dir, dst))

    # step8 analysis-layer files
    s8 = os.path.join(PROJ, "analysis", "step8_expansion")
    copies8 = [
        ("enrichment/enrichment_ora.csv", "enrichment_ora.csv"),
        ("enrichment/enrichment_gsea.csv", "enrichment_gsea.csv"),
        ("programs/program_scores.csv", "program_scores.csv"),
        ("programs/program_summary.csv", "program_summary.csv"),
        ("deconv/deconv_scores.csv", "deconv_scores.csv"),
        ("deconv/deconv_summary.csv", "deconv_summary.csv"),
        ("consensus_annotated.csv", "consensus_annotated.csv"),
        ("consensus_enrichment.csv", "consensus_enrichment.csv"),
        ("lr/lr_interactions_CRSwNP_vs_control.csv", "lr_interactions_CRSwNP_vs_control.csv"),
        ("lr/lr_interactions_CRSsNP_vs_control.csv", "lr_interactions_CRSsNP_vs_control.csv"),
    ]
    for src, dst in copies8:
        shutil.copy(os.path.join(s8, src), os.path.join(data_dir, dst))

    # de tables zip
    de_dir = os.path.join(s2, "de")
    zip_path = os.path.join(data_dir, "de_tables")
    shutil.make_archive(zip_path, "zip", de_dir)
    print("de_tables.zip bytes:", os.path.getsize(zip_path + ".zip"))

    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fns in os.walk(SITE) for f in fns)
    print("site total bytes:", total)
    print("i18n strings:", len(_STRINGS))

if __name__ == "__main__":
    main()
