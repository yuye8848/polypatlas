# PolypAtlas — CRSwNP Multi-omics Resource（网站工程说明）

> 工作名称可更名：全站唯一名称配置在 `web/build/build.py` 的 `WORKING_NAME` 变量；
> 改名后重新运行 `python3 build/build.py` 即可全站生效（v1.1 起双语支持随构建自动保留）。

## 中英双语（v1.1）

- 每页页眉有 `EN | 中文` 切换；首次加载默认英文；选择经 `localStorage` 跨页面/刷新保持。
- 全部用户文案登记在 `build/build.py` 的 `STRINGS`（key → (en, zh)）；页面以英文内联 + `data-i18n` 标记生成，词典内联在每页脚本中（无外部 JSON 请求，file:// 可用）；基因页动态字符串在 `gene_app.js` 的 `GS` 词典中。
- 不翻译：基因符号、GEO 编号、数据集原标题、数字、PMID、文件名。
- 详见 `i18n_report.md`。

## 目录

- `site/` —— 生成的静态网站（HTML/CSS/JS，纯静态，无构建框架，无后端）
- `build/build.py` —— 网站构建脚本（读 steps 1–4 的结果文件，生成 `site/`）
- `step5_report.md` —— 本步报告（中文）

## 网站页面

| 页面 | 功能 |
|---|---|
| index.html | 项目介绍、headline 数字、三层证据说明、诚实声明 |
| gene.html | 基因查询：bulk 16 队列 logFC/FDR + 条形图、单细胞 41 对比、空间两区室值（或“不在 CTA panel 中”说明） |
| cohorts.html | 16 个 bulk 队列、10 个单细胞数据集、空间数据集的元数据 + 逐条限制标注（黄色 ⚠ 块） |
| downloads.html | 结果表下载（证据矩阵、DE 全表、组成表、策展表等） |
| methods.html | 流程、已知限制全文、数据来源、作者占位符 |

## 重新生成

```bash
cd ~/workspace/sci-crswnp-resource/web/build
python3 build.py   # 需要 pandas；输出到 ../site/
```

构建产物 `site/data.js` 是预计算的基因数据（23,241 基因；bulk 16 队列、单细胞 41 对比、空间两区室），
纯前端查询无需后端；`site/data/` 为下载文件（56 MB 以内）。

## 上线（GitHub Pages）

本地已 `git init` 并提交首版（时间戳在 git 历史中）。发布为公开仓库的步骤：

```bash
cd ~/workspace/sci-crswnp-resource/web
gh auth login                       # 用户侧一次：浏览器授权
gh repo create polypatlas --public --source=. --push
gh api repos/{owner}/polypatlas/pages -X POST -f 'build_type=legacy' -f 'source[branch]=main' -f 'source[path]=/site'
# 完成后地址：https://{owner}.github.io/polypatlas/
```

注意：`site/` 是子目录，GitHub Pages 需把发布目录设为 `/site`。
