#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PolypAtlas build script — generates the static site from step 1-4 outputs.
Run:  python3 build.py
Output: ../site/ (the site), data copied to ../site/data/ (downloads)
Every number rendered on the site is copied from the step reports / result files,
never invented. Caveats are rendered next to the data they qualify.
"""
import csv, json, os, shutil, re
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(BASE))  # ~/workspace/sci-crswnp-resource
SITE = os.path.join(PROJ, "web", "site")
VERSION = "v1.0"
BUILD_DATE = date.today().isoformat()

# ---------------- cohort metadata (from step2_report.md, numbers exact) --------
BULK_COHORTS = [
    {"id": "GSE136825", "n": "息肉(75) vs 对照下鼻甲(28)", "method": "RNA-seq · DESeq2",
     "sig": "5,320", "note": "本宇宙最大的 CRSwNP bulk 队列；阳性对照 panel 行为正确（CLC +3.87）。"},
    {"id": "GSE179265", "n": "CRSwNP(17) vs 健康对照(7)", "method": "RNA-seq · DESeq2",
     "sig": "5,278", "note": "附加对比：美国 vs 日本息肉。阳性对照 7/8 显著上调（CLC +7.51）。"},
    {"id": "GSE338426", "n": "CRSwNP(14) vs 对照(8)", "method": "RNA-seq · DESeq2",
     "sig": "2,273", "note": "内型标签（嗜酸/非嗜酸）来自 deposited metadata。CLC +7.97。"},
    {"id": "GSE198950", "n": "CRSwNP(5) vs 非CRS(4)", "method": "RNA-seq · DESeq2",
     "sig": "3,141", "caveat": "组织混杂：病例为筛窦组织、对照为下鼻甲组织——IL33/POSTN 显著反向可能源于此，使用时必须注明。"},
    {"id": "GSE267331", "n": "dupilumab 治疗后 vs 前（47 对配对）", "method": "芯片 · limma 配对",
     "sig": "4,856", "note": "唯一的治疗纵向队列（SINUS-52 鼻刷）：CLC/POSTN/SERPINB2 显著下调，符合治疗逆转预期；安慰剂臂 0 个显著。"},
    {"id": "GSE189690", "n": "N-ERD(13) vs 非 N-ERD CRSwNP(13)", "method": "RNA-seq · DESeq2",
     "sig": "12", "caveat": "无健康对照：仅疾病亚型对比，不参与病例-对照方向先验。"},
    {"id": "GSE313186", "n": "毒素暴露 CRS(10) vs 未暴露对照(10)", "method": "RNA-seq · DESeq2",
     "sig": "106", "note": "退伍军人部署暴露队列；肥大细胞表型。"},
    {"id": "GSE213809", "n": "刺激后 NP-ILC2 vs 外周血 ILC2(14v14)", "method": "RNA-seq · DESeq2",
     "sig": "4", "note": "分选 ILC2 亚群图谱型，非病例对照队列设计。"},
    {"id": "GSE150846", "n": "鼻息肉 ILC2 vs 外周血 ILC2(3v3)", "method": "芯片 · limma",
     "sig": "606", "note": "分选 ILC2 亚群图谱型；n 极小。"},
    {"id": "GSE174681", "n": "息肉 ASC vs 外周血 naive B(3v4)", "method": "TMM · limma",
     "sig": "1,813", "note": "分选 B 细胞亚群图谱型，非病例对照队列设计。"},
    {"id": "GSE330761", "n": "CRSwNP-MCTC vs CRSsNP-MCTC(3v3)", "method": "txi counts · voom",
     "sig": "443", "caveat": "无健康对照；分选肥大细胞亚群图谱型（3v3）。"},
    {"id": "GSE194282", "n": "鼻息肉(7) vs 对照(7)", "method": "芯片 · limma",
     "sig": "251", "note": "对照含肿瘤旁正常组织；样本量小，功效有限。"},
    {"id": "GSE36830", "n": "CRSwNP(12) vs 钩突对照(6)", "method": "芯片 · limma",
     "sig": "0", "note": "表达矩阵为线性尺度，已 log2(x+1) 转换；0 个 FDR 显著为数据本底。"},
    {"id": "GSE69093", "n": "病例 vs 对照（校正细胞类型）", "method": "芯片 · limma+协变量",
     "sig": "0", "caveat": "原代培养细胞：全转录组 0 显著但 p 值富集于小 p 端，判为真实弱信号（非技术错误）。系列注册平台误标（Affymetrix），已按 Illumina HumanHT-12 v4 注释修正。"},
    {"id": "GSE70898_70900", "n": "息肉 T 细胞 vs 正常鼻黏膜 T 细胞(12v6)", "method": "芯片 · limma",
     "sig": "9,426", "note": "同研究跨系列（GSE70898+GSE70900）合并；短期 explant 培养；平台误标已修正。"},
    {"id": "GSE72713", "n": "CRSwNP(6) vs 正常对照(3)", "method": "FPKM · limma",
     "sig": "129", "note": "n 极小（3/3/3）；lncRNA+mRNA 混合文件。"},
]
BULK_IDS = [c["id"] for c in BULK_COHORTS]

SC_DATASETS = [
    {"id": "GSE235711", "cells": "55,827", "donors": "20", "design": "对照5 / CRSsNP5 / CRSwNP10",
     "note": "Liao Immunity 2025；完整组织图谱。CRSsNP vs 对照在供体水平几乎无显著基因（5v5，数据本底，非分析失败）。"},
    {"id": "GSE276503", "cells": "177,666", "donors": "29 供体单元", "design": "对照2 / CRSwNP27",
     "caveat": "对照仅 2 例（统计慎用）；4 个样本的存放端矩阵损坏已剔除；供体结构未声明。"},
    {"id": "GSE270953", "cells": "51,926", "donors": "10", "design": "息肉5 / 扁桃体5",
     "caveat": "对照为扁桃体（免疫学上与鼻黏膜差异大），解读须加 caveat；CITE-seq 臂未处理。"},
    {"id": "GSE249159", "cells": "42,041", "donors": "6", "design": "息肉3 / 外周血3",
     "note": "小鼠臂已排除；仅 CD4_T 满足 3v3 DE 条件。"},
    {"id": "GSE196169", "cells": "37,168", "donors": "13", "design": "AERD 单臂",
     "caveat": "存放数据无 CRSwNP 对照臂，已降级为单臂组成图谱；网站不列出该对比。"},
    {"id": "GSE202100", "cells": "38,514", "donors": "5", "design": "CRSwNP 单臂（上皮刷检）",
     "note": "tuft 信号（POU2F3/TRPM5）富集于 ionocyte 簇，未强行拆分，如实标注。"},
    {"id": "GSE324445", "cells": "30,954", "donors": "10", "design": "息肉6 / 外周血4",
     "caveat": "名义“分选 ILC2”，实测仅 36% 为真 ILC2、56% 为 CD4_T——网站展示实测组成，不用名义值。"},
    {"id": "GSE255544", "cells": "20,394", "donors": "7", "design": "CRSwNP 疾病单臂（淋巴细胞）",
     "note": "待核→转正（GSM 标题证实 CRSwNP，PMID 38589618）。"},
    {"id": "GSE156285", "cells": "10,803", "donors": "4", "design": "CRS 疾病单臂组成图谱",
     "note": "旧版 10x 注释缺若干上皮 marker，部分簇只能标 ambiguous。"},
    {"id": "GSE179292", "cells": "10,961", "donors": "4", "design": "CRSwNP 分选 T 细胞组成图谱",
     "note": "分选 T 细胞制剂。"},
]

SPATIAL_INFO = {
    "id": "GSE235714", "roi": 40, "donors": "10（CRSwNP 6 / 对照 4）",
    "panel": "1,480 基因（Nanostring DSP Human CTA；实测，非全转录组）",
    "caveats": [
        "供体级差异分析两区室 FDR<0.05 均为 0——空间层为“区室定位/展示层”，不是疾病差异的独立证据层；只展示描述性区室 logFC，不做一致性声称。",
        "疾病与组织完全混杂：CRSwNP 供体全为鼻息肉组织，对照全为筛窦组织。",
        "GSM7508390（CRSwNP_8 CD45+ ROI2）QC 标记 'Low Surface Area'（保留未剔除）。",
        "panel 覆盖率：bulk top100 基因并集仅 14.6% 在 panel 中；不在 panel 的基因（如 CLC/CCL26/POSTN/ALOX15）明确返回“不在 CTA panel 中”。",
    ],
}

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

# ---------------- site pages --------------------------------------------
CSS = """
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:1100px;margin:0 auto;padding:18px;color:#222;line-height:1.65;background:#fafafa}
h1{font-size:26px;border-bottom:2px solid #1a6fb5;padding-bottom:8px}
h2{font-size:20px;color:#1a6fb5;margin-top:34px}
h3{font-size:16px;margin-top:22px}
nav{background:#1a6fb5;padding:10px 18px;border-radius:8px;margin-bottom:18px}
nav a{color:#fff;margin-right:22px;text-decoration:none;font-weight:bold}
nav a:hover{text-decoration:underline}
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

NAV = """<nav><a href="index.html">首页</a><a href="gene.html">基因查询</a><a href="cohorts.html">队列与数据集</a><a href="downloads.html">数据下载</a><a href="methods.html">方法与限制</a></nav>"""
WORKING_NAME = "PolypAtlas — CRSwNP Multi-omics Resource"
DISCLAIMER = ('<div class="disc"><b>研究用途声明 / Research use only</b>：'
              '本站为鼻息肉（CRSwNP）公开转录组数据的整合查询资源，仅供科研参考，'
              '不提供临床诊断、患病概率或治疗建议。所有数值均为公开数据的统一再分析结果，'
              '每个队列的已知限制均标注在数据旁。</div>')
FOOTER = (f'<div class="footer">{WORKING_NAME}（工作名称，可更名） · {VERSION} · 构建日期 {BUILD_DATE} · '
          '数据来源：GEO 公开数据（各系列见“队列与数据集”页的 PMID/GEO 链接） · '
          '作者/联系方式：[待填]</div>')

def page(title, body):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {WORKING_NAME}</title><link rel="stylesheet" href="style.css"></head>
<body>{NAV}<h1>{WORKING_NAME}</h1><h2>{title}</h2>{body}{FOOTER}</body></html>"""

def build_index():
    h = HEADLINE
    stats = "".join(
        f'<div class="stat"><b>{v}</b>{k}</div>'
        for k, v in [
            ("策展 GSE 系列", h["series_curated"]),
            ("核心集", h["series_core"]),
            ("普查样本总数", h["samples_curated"]),
            ("bulk 差异队列", h["bulk_cohorts"]),
            ("bulk 基因×队列证据", f'{h["bulk_genes"]}×{h["bulk_cohorts"]}'),
            ("单细胞数据集", h["sc_datasets"]),
            ("单细胞（细胞数）", h["sc_cells"]),
            ("单细胞供体单元", h["sc_donors"]),
            ("空间 ROI", h["spatial_roi"]),
            ("空间 panel 基因", h["spatial_genes"]),
            ("自带内型标签系列", h["endotype_series"]),
        ])
    body = (DISCLAIMER
        + f'<p>本资源对 GEO 全部 {h["series_curated"]} 个慢性鼻窦炎/鼻息肉人类数据集逐个策展（核心集 {h["series_core"]}），'
          '对合格的 bulk 队列逐个统一重跑差异分析、对单细胞数据集统一注释到一套细胞类型词表、'
          '对 GeoMx 空间数据按区室整理，与 bulk/单细胞三方对齐。所有结果均可在线查询与下载。</p>'
        + stats
        + '<h3>三层证据</h3><ul>'
        '<li><b>Bulk</b>：16 个队列逐队列差异分析（30 个对比），19,266 蛋白编码基因×队列证据矩阵。跨平台不合并表达矩阵，只在结果层汇总（方向/效应量/显著性）。</li>'
        '<li><b>单细胞</b>：10 个数据集统一注释（25 类细胞词表），476,254 细胞、105 供体单元；差异统计以供体为单位（pseudobulk），17,631 基因×41 对比。</li>'
        '<li><b>空间</b>：GSE235714 GeoMx 40 ROI（CD45+ 免疫 / PanCK+ 上皮区室），1,480 基因 CTA panel——<b>供体级差异分析两区室 FDR&lt;0.05 均为 0</b>，空间层定位为区室定位/展示层，不作为独立证据层；只展示描述性值，见区室 logFC 与混杂声明。</li></ul>'
        '<h3>快速开始</h3><p>查一个基因（如 CLC、IL33）：<a href="gene.html"><b>基因查询页 →</b></a>；'
        '浏览全部数据集与已知限制：<a href="cohorts.html"><b>队列与数据集 →</b></a>；'
        '批量取数：<a href="downloads.html"><b>数据下载 →</b></a>。</p>'
        + '<div class="caveat"><b>诚实声明（使用前请读）</b>：各队列的设计差异很大——组织混杂（GSE198950）、无健康对照（GSE189690、GSE330761）、'
          '原代培养弱信号（GSE69093）、扁桃体对照（GSE270953）、AERD 单臂（GSE196169）等。每个队列的限制标注在其数据旁，“队列与数据集”页有全表。</div>')
    return page("首页", body)

def build_gene():
    quick = " ".join(f'<button onclick="searchGene(\'{g}\')">{g}</button>' for g in QUICK_GENES)
    body = (DISCLAIMER
        + '<div class="card"><input type="text" id="q" placeholder="输入基因符号，如 CLC" onkeydown="if(event.key===\'Enter\')searchGene()">'
          ' <button onclick="searchGene()">查询</button></div>'
        + f'<p>常用基因：{quick}</p><div id="result"></div>'
        + '<script src="data.js"></script>\n<script src="gene_app.js"></script>')
    return page("基因查询", body)

def build_cohorts():
    rows = []
    for c in BULK_COHORTS:
        tag = f'<div class="caveat"><b>⚠ 限制：</b>{c["caveat"]}</div>' if c.get("caveat") else ""
        note = f'<br><span style="font-size:13px;color:#555">{c.get("note","")}</span>' if c.get("note") else ""
        rows.append(f'<tr><td><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={c["id"].split("_")[0]}">{c["id"]}</a></td>'
                    f'<td>{c["n"]}</td><td>{c["method"]}</td><td>{c["sig"]}</td>'
                    f'<td>{note}{tag}</td></tr>')
    bulk_tbl = ("<h3>Bulk 差异分析队列（16）</h3>"
                '<table><tr><th>系列</th><th>主对比（case vs control）</th><th>方法</th><th>FDR&lt;0.05 基因数</th><th>备注 / 限制</th></tr>'
                + "".join(rows) + "</table>")
    sc_rows = []
    for d in SC_DATASETS:
        tag = f'<div class="caveat"><b>⚠ 限制：</b>{d["caveat"]}</div>' if d.get("caveat") else ""
        note = f'<br><span style="font-size:13px;color:#555">{d.get("note","")}</span>' if d.get("note") else ""
        sc_rows.append(f'<tr><td><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={d["id"]}">{d["id"]}</a></td>'
                       f'<td>{d["cells"]}</td><td>{d["donors"]}</td><td>{d["design"]}</td>'
                       f'<td>{note}{tag}</td></tr>')
    sc_tbl = ("<h3>单细胞统一注释数据集（10）</h3><p>共 476,254 细胞、105 供体单元；注释到统一 25 类细胞词表；差异统计以供体为单位（pseudobulk）。</p>"
              '<table><tr><th>系列</th><th>细胞数</th><th>供体</th><th>设计</th><th>备注 / 限制</th></tr>'
              + "".join(sc_rows) + "</table>")
    sp = SPATIAL_INFO
    sp_sec = ("<h3>空间数据集（1）</h3>"
              f'<p><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={sp["id"]}">{sp["id"]}</a> GeoMx DSP：'
              f'{sp["roi"]} ROI × {sp["donors"]} 供体；panel {sp["panel"]}。</p>'
              + "".join(f'<div class="caveat"><b>⚠ 空间层限制：</b>{c}</div>' for c in sp["caveats"]))
    other = ("<h3>其他</h3><ul>"
             "<li>待核集 11 个系列：每个都有具名待核项，未达到 core 标准，不进入查询（详见策展报告）。</li>"
             "<li>剔除 25 个系列：superseries 父记录、健康体外模型、邻近疾病（过敏性鼻炎/哮喘）、非表达组学等，逐条原因见策展表。</li>"
             "<li>3 个 ncRNA 阵列核心系列（GSE169375/GSE169376/GSE32300）：分子类型不同，本轮未进入 bulk DE；结果文件另行提供。</li></ul>")
    body = DISCLAIMER + bulk_tbl + sc_tbl + sp_sec + other
    return page("队列与数据集", body)

def build_downloads():
    items = [
        ("evidence_matrix_logFC.csv", "Bulk：19,266 蛋白编码基因 × 16 队列 logFC（主对比；探针按 min-p 塌缩）。"),
        ("evidence_matrix_FDR.csv", "Bulk：同上矩阵的 BH-FDR。"),
        ("de_tables.zip", "Bulk：30 个对比的逐队列全量差异结果（symbol, logFC, p, FDR）。"),
        ("runlog.csv", "Bulk：30 个对比的 n、尺度裁决、方法、状态记录。"),
        ("controls_panel.csv", "Bulk：8 基因阳性对照 panel（CLC/CCL26/CCL13/IL33/TSLP/POSTN/SERPINB2/ALOX15）逐队列数值。"),
        ("celltype_evidence_matrix.csv", "单细胞：17,631 基因 × 41 个细胞类型级 pseudobulk 对比（logFC+FDR）。"),
        ("composition_all.csv", "单细胞：1,431 行 dataset×donor×group×celltype×fraction 组成表。"),
        ("alignment_table.csv", "空间：1,480 panel 基因 × 39 列（空间两区室 + 16 bulk 队列 + 同研究单细胞平均）。"),
        ("roi_metadata.csv", "空间：40 ROI 元数据（含 QC 标记 GSM7508390）。"),
        ("curation_table.csv", "策展总表：66 个系列逐个定性（verdict/证据注记）。"),
    ]
    lis = "".join(f'<li><a href="data/{f}">{f}</a> —— {d}</li>' for f, d in items)
    body = (DISCLAIMER + "<ul>" + lis + "</ul>"
            + '<div class="caveat"><b>使用说明</b>：所有文件均为统一再分析产出；每个文件的生成口径见“方法与限制”页；'
              '已注释的 h5ad 对象体积大，未放上本站（可联系作者获取）。</div>')
    return page("数据下载", body)

def build_methods():
    body = (DISCLAIMER
        + "<h3>流程</h3><ol>"
        "<li><b>普查与策展</b>：GEO 人类 CRS/鼻息肉查询 66 系列逐个验明（组织/分组/平台/样本量），定级 core/pending/excluded，逐条有证据注记；内型标签只认 deposited metadata，不推测。</li>"
        "<li><b>Bulk 统一重分析</b>：逐队列独立差异分析（counts→DESeq2；连续值→limma；配对→配对模型），先做尺度三方核查；探针按 min-p 塌缩到 symbol；跨平台只在结果层汇总，不合并表达矩阵。</li>"
        "<li><b>单细胞统一注释</b>：leiden 聚类 + 规范 marker 打分到统一 25 类词表（全基因矩阵打分，非 HVG 子集）；出结果前先过阳性对照断言（管家/上皮/免疫标志）；差异统计以供体为单位（pseudobulk）。</li>"
        "<li><b>空间</b>：GeoMx 按区室整理；6v4 供体下 FDR 全为 0，故空间层只作区室定位/展示层，不做独立证据；展示描述性值并固定标注低功效与组织混杂。</li>"
        "<li><b>网站</b>：预计算结果做成静态查看器；每处数据的已知限制标注在数据旁。</li></ol>"
        "<h3>已知限制（全文）</h3><ul>"
        "<li>内型（嗜酸/非嗜酸）标签只有 6 个系列自带 deposited metadata，且多为小样本——本站不做组织嗜酸计数的预测，只做程序/基因层面的证据展示。</li>"
        "<li>6 个 bulk 队列 n≤7/组或功效低（GSE72713、GSE150846、GSE174681、GSE330761、GSE36830、GSE194282），证据矩阵中权重应下调。</li>"
        "<li>GSE198950 组织混杂、GSE69093 真实弱信号、GSE189690/GSE330761 无健康对照——跨队列比较时需分层看，不可直接合并。</li>"
        "<li>GSE158277（配对 N-ERD，n=20）GEO 只有结果表无表达矩阵，未能重分析；若获原始数据可补入。</li>"
        "<li>单细胞：分选制剂（GSE179292/GSE324445/GSE270953/GSE255544 等）组成不代表整组织；GSE324445 名义分选与实测组成不符；GSE270953 对照为扁桃体；GSE276503 对照仅 2 例。</li>"
        "<li>空间：见“队列与数据集”页的四条空间层限制。</li>"
        "<li>公开数据二次分析：原始研究的伦理批准由各原始研究承担；本站不收集任何新样本与个人信息。</li></ul>"
        "<h3>数据来源</h3><p>全部来自 GEO 公开系列（各系列 PMID 与 GEO 链接见“队列与数据集”页）；"
        "策展报告、重分析报告与本网站构建脚本随代码仓库公开，全部数字可复现。</p>"
        "<h3>作者与联系</h3><p>作者：[待填] · 通讯：[待填] · 引用本资源：[待填]</p>")
    return page("方法与限制", body)

GENE_APP_JS = r"""
const BULK = DATA.coho, SCN = DATA.scl, GENES = DATA.genes;
function fmt(v, d){ if(v==null) return '<span style="color:#aaa">—</span>'; return Number(v).toFixed(d); }
function badge(f){ if(f==null) return ''; if(f<0.05) return '<span class="badge sig">FDR<0.05</span>'; return '<span class="badge nonsig">ns</span>'; }
function searchGene(g0){
  let q = (g0 || document.getElementById('q').value || '').trim().toUpperCase();
  const box = document.getElementById('result');
  if(!q){ box.innerHTML = '<p>请输入基因符号。</p>'; return; }
  let key = Object.keys(GENES).find(k => k.toUpperCase() === q);
  if(!key){ // prefix suggestions
    let cand = Object.keys(GENES).filter(k => k.toUpperCase().startsWith(q)).slice(0,20);
    box.innerHTML = '<p>未找到 <b>'+q+'</b>。' + (cand.length? '可能：'+cand.map(c=>`<a href="#" onclick="searchGene('${c}');return false;">${c}</a>`).join('、') : '无相似符号。') + '</p>';
    return;
  }
  document.getElementById('q').value = key;
  const r = GENES[key];
  let html = '<div class="card"><h3>'+key+'</h3>';
  // bulk table + chart
  html += '<h3>Bulk：16 队列（主对比）</h3><table><tr><th>队列</th><th>logFC</th><th>FDR</th><th></th></tr>';
  const vals = [];
  if(r.b){
    BULK.forEach((c,i)=>{
      const e = r.b[i]; vals.push(e?e[0]:null);
      html += '<tr><td>'+c.id+'<br><span style="font-size:12px;color:#666">'+c.n+'</span>'
        + (c.caveat? '<br><span class="badge warn">⚠ 限制见下</span>' : '') + '</td>'
        + '<td>'+fmt(e?e[0]:null,3)+'</td><td>'+fmt(e?e[1]:null,4)+'</td><td>'+badge(e?e[1]:null)+'</td></tr>';
    });
  } else html += '<tr><td colspan="4">该基因不在 bulk 证据矩阵中（未测得）。</td></tr>';
  html += '</table>';
  const caveats = BULK.filter(c=>c.caveat && r.b && BULK.indexOf(c)<r.b.length && r.b[BULK.indexOf(c)]);
  const shown = [...new Set(caveats.map(c=>'<div class="caveat"><b>⚠ '+c.id+' 限制：</b>'+c.caveat+'</div>'))];
  if(shown.length) html += shown.join('');
  html += '<h3>Bulk logFC 条形图</h3><canvas id="cv" width="900" height="340"></canvas></div>';
  // sc table
  html += '<div class="card"><h3>单细胞：细胞类型级对比</h3>';
  if(r.s){
    html += '<table><tr><th>对比（数据集 · 细胞类型 · 设计）</th><th>logFC</th><th>FDR</th><th></th></tr>';
    Object.keys(r.s).forEach(i=>{
      const e = r.s[i];
      html += '<tr><td>'+SCN[+i]+'</td><td>'+fmt(e[0],3)+'</td><td>'+fmt(e[1],4)+'</td><td>'+badge(e[1])+'</td></tr>';
    });
    html += '</table>';
  } else html += '<p>该基因不在单细胞证据矩阵中（未测得）。</p>';
  html += '</div>';
  // spatial
  html += '<div class="card"><h3>空间（GeoMx，GSE235714）</h3>';
  if(r.sp){
    html += '<table><tr><th>区室</th><th>logFC（供体级描述值）</th><th>FDR</th></tr>'
      + '<tr><td>CD45+ 免疫区室</td><td>'+fmt(r.sp[0],3)+'</td><td>'+fmt(r.sp[1],4)+'</td></tr>'
      + '<tr><td>PanCK+ 上皮区室</td><td>'+fmt(r.sp[2],3)+'</td><td>'+fmt(r.sp[3],4)+'</td></tr></table>'
      + '<div class="caveat"><b>⚠ 空间层限制：</b>两区室供体级 FDR&lt;0.05 均为 0（6v4 供体），此为描述性值，非独立证据；'
      + '且疾病与组织完全混杂（CRSwNP=息肉组织 vs 对照=筛窦组织）。</div>';
  } else html += '<p>该基因<b>不在 GeoMx CTA panel（1,480 基因）中</b>——无空间数据，非缺失值。</p>';
  html += '</div>';
  box.innerHTML = html;
  drawChart(vals);
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
"""

# ---------------- main ----------------------------------------------------
def main():
    os.makedirs(SITE, exist_ok=True)
    data_dir = os.path.join(SITE, "data")
    os.makedirs(data_dir, exist_ok=True)

    genes, sc_labels, n_genes = build_gene_data()
    print(f"genes in union: {n_genes}")

    data_js = {
        "version": VERSION, "build_date": BUILD_DATE,
        "coho": [{"id": c["id"], "n": c["n"], "caveat": bool(c.get("caveat"))} for c in BULK_COHORTS],
        "scl": sc_labels, "genes": genes,
    }
    js_text = "const DATA = " + json.dumps(data_js, separators=(",", ":"), ensure_ascii=False) + ";"
    with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as fh:
        fh.write(js_text)
    print("data.js bytes:", len(js_text.encode("utf-8")))

    with open(os.path.join(SITE, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    with open(os.path.join(SITE, "gene_app.js"), "w", encoding="utf-8") as fh:
        fh.write(GENE_APP_JS)

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(build_index())
    with open(os.path.join(SITE, "gene.html"), "w", encoding="utf-8") as fh:
        fh.write(build_gene())
    with open(os.path.join(SITE, "cohorts.html"), "w", encoding="utf-8") as fh:
        fh.write(build_cohorts())
    with open(os.path.join(SITE, "downloads.html"), "w", encoding="utf-8") as fh:
        fh.write(build_downloads())
    with open(os.path.join(SITE, "methods.html"), "w", encoding="utf-8") as fh:
        fh.write(build_methods())

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

    # de tables zip
    de_dir = os.path.join(s2, "de")
    zip_path = os.path.join(data_dir, "de_tables")
    shutil.make_archive(zip_path, "zip", de_dir)
    print("de_tables.zip bytes:", os.path.getsize(zip_path + ".zip"))

    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fns in os.walk(SITE) for f in fns)
    print("site total bytes:", total)

if __name__ == "__main__":
    main()
