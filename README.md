# PolypAtlas — CRSwNP Multi-omics Resource

**Live resource: https://polyp.erbihou.org/**

PolypAtlas is a curated, harmonized multi-omics resource for chronic rhinosinusitis with nasal polyps (CRSwNP), built entirely from public data. It integrates the public human CRS / nasal-polyp transcriptomic datasets catalogued on GEO (66 series curated; 30 core datasets), spanning bulk transcriptomics, single-cell RNA-seq and spatial transcriptomics, reprocessed under one uniform pipeline so that any gene can be compared across cohorts, cell types and tissue compartments.

鼻息肉（CRSwNP）多组学公共数据资源：策展 GEO 全部 66 个人类 CRS/鼻息肉系列，统一流程重处理 bulk、单细胞与空间转录组，支持按基因跨队列、跨细胞类型、跨组织区室查询。网站为中英双语，默认英文。

## Contents

- **Bulk transcriptomics:** 16 cohorts, 30 contrasts, 19,266 genes
- **Single-cell RNA-seq:** 10 datasets, 476,254 cells, 105 donors
- **Spatial transcriptomics (GeoMx):** polyp vs control tissue compartments
- **Built-in validation:** marker direction recovery 87.5%; dupilumab reversal in 7 of 8 markers

## Website features

- **Gene lookup** — bulk logFC/FDR across 16 cohorts, single-cell contrasts, and spatial compartment values for any gene, plus pathway membership and consensus annotations
- **Pathway query** — search an enriched pathway and see in which cohorts and cell types it appears
- **Cohort browser** — full metadata for every dataset, with each dataset's limitations stated next to its data
- **Downloads** — evidence matrix, differential-expression tables, composition tables and the curation table
- **Methods** — the full pipeline and known limitations, stated in full

## Data availability

All processed data are archived on Zenodo (CC BY 4.0): **DOI [10.5281/zenodo.23448780](https://doi.org/10.5281/zenodo.23448780)**. The same tables are also available directly from the website's download page.

## Citation

If you use PolypAtlas in your work, please cite:

> PolypAtlas: a curated multi-omics resource for chronic rhinosinusitis with nasal polyps. https://polyp.erbihou.org/ — archived data: Zenodo, DOI 10.5281/zenodo.23448780.

## Repository layout

- `build/` — the static-site generator
- `site/` — the generated website (served via the `gh-pages` branch at the address above)

## Contact

Peiliang Lei (of@live.com), Department of Otolaryngology, The Third Hospital of Shijiazhuang, Shijiazhuang, Hebei, China.
