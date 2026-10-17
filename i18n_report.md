# i18n 报告：PolypAtlas 中英双语（v1.1，默认英文）

日期：2026-10-18 · 构建器：`web/build/build.py`（v1.1）· 构建耗时约 11 秒

## 一、机制

- 全部用户文案登记在 `build.py` 顶部 `STRINGS`（key → (en, zh)，共 163 条；数据驱动的队列 note/caveat 也在此登记，队列页与动态基因页复用同一 key，两种语言文本一致）。
- 页面以**英文内联** + `data-i18n="key"` 标记生成；每页尾部内联脚本嵌入完整双语词典（JSON），`pa_setLang(l)` 批量替换 `innerHTML`；placeholder 用 `data-i18n-ph`。
- 语言选择存 `localStorage['pa_lang']`，跨页面/刷新保持；**首次加载默认英文**：HTML 内联默认文本即英文（无闪烁），`<html lang="en">`，JS 取 `localStorage.getItem('pa_lang') || 'en'`。
- 基因页动态字符串在生成的 `gene_app.js` 内另有一份 `GS` 词典（20 key）+ caveat 复用 `CAV`（4 条 bulk 限制块）；`DATA.coho` 每条记录带 `n_en`/`n_zh` 设计字符串；语言切换时通过 `window.PA_langChanged` 钩子重绘当前查询结果。
- 纯前端、无后端、无外部 JSON 请求，file:// 与静态托管均可运行；`WORKING_NAME` 改名机制不变（两语言下名称相同）。

## 二、字符串清单（按页面）

| 页面 | data-i18n 标记数 | 覆盖范围 |
|---|---|---|
| index.html | 30 | 导航、标题、用途声明、介绍段、11 个统计标签、三层证据、快速开始、诚实声明、页脚 |
| gene.html | 13 | 导航、标题、用途声明、搜索框 placeholder、查询按钮、"常用基因"标题、页脚 |
| cohorts.html | 87 | 导航、标题、用途声明、3 个分节标题、两组表头、16 队列设计字符串、全部 note/caveat 块（16 bulk + 10 sc + 4 spatial）、"其他"3 条、页脚 |
| downloads.html | 22 | 导航、标题、用途声明、10 个文件产出口径说明、使用说明、页脚 |
| methods.html | 29 | 导航、标题、用途声明、流程 5 条、已知限制 7 条、数据来源、作者占位、页脚 |
| gene_app.js | GS 20 key + CAV 4 | 空查询/未命中/候选提示、表标题与表头、"未测得"/"不在 panel"两种缺失态、空间限制块、区室名、限制徽标 |

英文为对原中文文案的忠实翻译（原文案源自 steps 1–4 报告），翻译中未增删任何主张。

## 三、验证结果

- (a) 5 页全部含双语词典（163 key）、EN|中文切换器与接线；引用的 key 全部有定义、en/zh 均非空；词典值中无 `</script>` 注入风险。
- (b) 基因页动态字符串：`gs()` 调用的 19 个 key 全部存在、en/zh 俱全；`PA_langChanged` 重绘钩子与 localStorage 读取正常；搜索框 placeholder 已本地化；快捷基因按钮均为基因符号（不翻译）。
- (c) 数据完整性抽查（直接模拟 JS 逻辑读 data.js）：CLC 在 GSE136825 为 [3.866, 7.344e-06]；IL33 在 GSE198950 为 [-2.112, 0.008374]；IL33 空间 FDR 为 0.9988/0.9979（与 step4 报告一致）；CLC 无空间条目，"不在 GeoMx CTA panel"消息在两种语言下均正确返回；GSE198950 限制块两种语言文本与源报告一致。
- (d) 默认英文：`<html lang="en">` + 内联默认文本为英文 + JS 缺省 `'en'`。无 localStorage 时首屏即英文，无闪烁。

## 四、未翻译项及原因

- 基因符号、GEO 编号、原始数据集标题、数字、PMID、文件名：按任务要求不翻译。
- `FDR<0.05` / `ns` 表格徽标：通用统计符号，两语言通用。
- 图表内坐标轴队列标签为 GEO 编号，不翻译。

## 五、已知事项

- 初期构建曾发现各页面内联词典快照时机问题（index/gene 页缺少 `n_*`/`sc_design_*` 键）——已修复为模块级统一登记，5 页词典一致。
- GitHub 仍未登录：未推送；公开上线仍是用户侧步骤（见 README）。
