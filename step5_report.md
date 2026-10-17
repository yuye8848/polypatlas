# 第 5 步报告：网站构建与上线（step 5 · web）

日期：2026-10-18（构建日期按 Asia/Shanghai）
状态：**网站已建成、本地提交已落盘（时间戳已定）；公开上线待用户侧一次 GitHub 授权。**

## 一、建成内容

工作名称：PolypAtlas — CRSwNP Multi-omics Resource（工作名，可在 `build/build.py` 的 `WORKING_NAME` 一处更名，全站再生效）。

| 页面 | 内容 |
|---|---|
| index.html | 项目介绍、headline 数字、三层证据说明、诚实声明、研究用途声明 |
| gene.html | 基因查询：bulk 16 队列 logFC/FDR 表 + 条形图、单细胞 41 对比表、空间两区室值（或明确的“不在 CTA panel 中”说明）；缺层显示“未测得”而非空白 |
| cohorts.html | 16 个 bulk 队列、10 个单细胞数据集、1 个空间数据集的元数据（n/设计/方法/PMID/GEO 链接）+ 逐条限制标注（黄色 ⚠ 块，数据旁出现） |
| downloads.html | 10 个结果文件下载，各带一行产出口径说明 |
| methods.html | 流程、已知限制全文、伦理声明（公开数据二次分析，不收集新样本）、数据来源、作者占位符 [待填] |

**headline 数字（全部来自 steps 1–4 报告，无一编造）**：66 系列策展 / 30 核心 / 2,046 普查样本；bulk 16 队列 30 对比；单细胞 10 数据集 476,254 细胞 105 供体单元；空间 40 ROI 10 供体；自带内型标签 6 系列；唯一治疗队列 GSE267331。

**限制展示纪律**：GSE198950 组织混杂、GSE189690/GSE330761 无健康对照、GSE69093 真实弱信号+平台误标已修正、GSE270953 扁桃体对照、GSE196169 AERD 单臂降级、GSE276503 对照 n=2 + 存放端 4 样本损坏、GSE324445 名义分选与实测组成不符、GSE202100 tuft 标注说明、空间 6v4 低功效 + 疾病/组织完全混杂 + GSM7508390 QC 警告——全部已在 cohorts.html 的数据旁与 gene.html 的查询结果中标注。

**校验**：数据层已做机查——CLC bulk GSE136825 +3.866（与 step2 报告 +3.87 一致）、GSE198950 IL33 −2.112（与 INVESTIGATE 标记一致）、空间 CLC 返回“不在 panel 中”（与 panel 覆盖声明一致）、IL33/TSLP 空间 FDR≈0.9988（与“FDR≈1 无信号”一致）。

## 二、工程

- 构建脚本：`web/build/build.py`（pandas；11 秒生成全站），产物 `web/site/`；基因数据预计算为 `site/data.js`（8.9 MB，23,241 基因；bulk 16 队列、单细胞 41 对比、空间两区室；纯前端查询，无后端，file:// 与任何静态托管均可运行）。
- 下载文件 `site/data/`：10 个 CSV + de_tables.zip；全站 56 MB（<200 MB 上限）。h5ad 对象未上站（体积大，页面标注“可联系作者获取”）。
- git：`web/` 已 `git init`，首版已提交（commit bc38543，2026-10-17 17:59 UTC = 2026-10-18 01:59 CST），本地时间戳已定。

## 三、上线状态：被一次用户侧授权卡住

- GitHub 可达（api.github.com 200），但本机 `gh` **未登录任何 GitHub 账号**（`gh auth status`：未登录）。
- VPS（ssh vps8v8）从本环境不可达（代理连接被重置），无法经 VPS 镜像。
- **未推送、未建公开仓库、没有线上 URL——未伪造。**

**用户侧唯一需要做的动作**（三条命令，详见 `web/README.md`）：

```bash
cd ~/workspace/sci-crswnp-resource/web
gh auth login                       # 浏览器授权一次
gh repo create polypatlas --public --source=. --push
# 然后在 GitHub 网页把 Pages 发布目录设为 /site（或我回来执行 gh api 开通）
```

完成后地址：`https://{用户名}.github.io/polypatlas/`。仓库名为 polypatlas（备选 crswnp-resource；建库时可定）。

## 四、已知限制

- 作者/联系方式/引用格式为占位符 [待填]，待用户提供。
- build_date 取 Asia/Shanghai 日期（2026-10-18），与用户日历一致。
- Zenodo 快照（DOI 化）未做——需要用户侧 Zenodo/GitHub 联动，建议论文投稿前补。
