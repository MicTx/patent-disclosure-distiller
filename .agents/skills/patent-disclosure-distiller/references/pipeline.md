# 可执行生成流水线

本目录的运行时把一个已经整理好的 `DisclosurePackage` JSON 当作内容真源。它负责一致地生成 Markdown、Word、附图源稿/预览和 `manifest.json`；它不从自然语言猜测技术事实，也不替代专利检索、实验或代理师审查。

## 目录与入口

```text
schemas/disclosure-package.schema.json   输入契约（机器可读说明）
scripts/pipeline.py                      校验、图稿、Markdown、DOCX、manifest
scripts/generate_disclosure.py           生成 CLI
scripts/validate_disclosure.py           输入/产物校验 CLI
examples/map-preload/package.json        可复现的完整示例
tests/test_pipeline.py                   正负样本和 DOCX 包检查
```

先生成再验证：

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json
python3 .agents/skills/patent-disclosure-distiller/scripts/generate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json \
  /tmp/disclosure-output
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py \
  /tmp/disclosure-output
```

全量测试：

```bash
python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v
```

## 输入契约

顶层必须有 `package_version=1.0`、`metadata`、`evidence`、`sections`、`figures`、`questions` 和 `audit`。`FULL_DISCLOSURE` 还必须声明 `mode_contract`，并包含交付说明与证据范围、主题与摘要、技术领域、背景技术、技术问题、系统边界与主链、总体方案、模块与参数作用域、实施例、有益效果与验证边界、附图说明 11 类章节，且至少声明 `system`、`flow`、`sequence` 三张有节点和边的附图。`TARGETED_SECTION` 使用 `requested_sections`，`REWRITE_AUDIT` 使用 `rewrite_audit`，`INTAKE_DRAFT` 至少有一个待确认问题。

`FULL_DISCLOSURE` 的每张图必须声明 `source_image`、`generation_method`（`imagegen` 或 `ppt`）和生成提示/绘制说明 `prompt`。底图必须来自项目内的 imagegen 资产或 PPT 导出文件；不得把代码原生框图当作最终专利图。`figure_output_mode=spec_only` 时只生成附图方案和 manifest，不复制或嵌入实际图；`rendered` 才会复制底图并叠加确定性标签。

每个正文段落或列表块都要有 `evidence` 引用；每条证据只能使用一个主标签：`F` 材料事实、`C` 实际核验、`I` 推导、`A` 工作假设、`Q` 待确认、`L` 法律审查。`audit.p0` 非空时生成器拒绝产出，避免把未关闭的阻断问题包装成完整交付。

正文通过 `figure_ref` 回指 `figure_id`。每个 FigureSpec 都要有 `type/title/caption/labels/used_by/evidence/nodes/edges`，节点 ID 必须唯一，边必须引用已有节点；`sequence` 类型生成泳道和消息箭头，其他类型生成有向关系图。`spec_only` 模式输出附图方案，不输出实际 SVG/PNG；`rendered` 模式才输出同名 SVG 源稿和 PNG 预览并嵌入 Word。

## 输出与证据边界

`spec_only` 产物目录包含 `disclosure.md`、`disclosure.docx`、`figure-plan.md` 和 `manifest.json`，不包含实际图像；`rendered` 产物才包含 `figures/*.svg`、`figures/*.png`。manifest 保存输入摘要、章节、证据计数、图号/图题/生成方式/提示词/底图路径、SHA-256、渲染模式和审计状态。校验器会按模式检查文件存在、正文是否回指每张图、DOCX 媒体数量是否一致、DOCX 是否携带批注。

Word 默认采用 A4、`Hiragino Sans GB` 中文字体、标题层级、表格网格、页眉、页码字段和图题样式；字体常量集中在 renderer 中，后续可替换为代理机构模板字体。该契约证明结构和媒体关系，不证明在所有 Word/WPS 版本中的分页像素完全一致；需要代理机构固定模板或 PDF 逐页视觉验收时，应增加后续模板适配任务。

要复刻样例 DOCX，使用：

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/generate_disclosure.py \
  <package.json> <output-dir> \
  --reference-docx sample/一种基于马尔可夫链的地图瓦片及范围数据预加载方法.docx
```

`sample_fidelity` 使用样例的页尺寸、页眉页脚、段落直接格式、编号 donor、字体和符号规则生成新内容；`sample_exact` 逐字复制样例 DOCX，并以 SHA-256 证明基线一致。样例原始正文的 Unicode 下标、箭头、希腊字母和其他符号必须以原始字符串保留，不能改写成近似 ASCII。

效果百分比、外部专利差异、空间坐标、缓存并发和更新公式若没有材料支持，必须在输入中标为 `[Q]`/`[I]` 并进入 questions；示例中的“受限底稿”状态不会把这些内容升级为已验证结论。
