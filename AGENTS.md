# 本项目工程事实

## 分层与入口

- `distillation/` 只保存样例 DOCX 的证据抽取、写作模型和质量门研究，不是运行时代码；`sample/` 的原始 DOCX 保持只读基线。
- `.agents/skills/patent-disclosure-distiller/references/` 保存人工写作规则和字段模板；可执行入口在同目录的 `scripts/`。
- `schemas/` 描述 `DisclosurePackage`，`scripts/pipeline.py` 是唯一内容转换真源，`examples/` 提供可复现输入，`tests/` 负责机器验收。
- 依赖方向固定为：输入 schema → validator → Markdown/DOCX/图稿 renderer → manifest；renderer 不从散文规则或样例 DOCX 反向猜字段。

## 数据契约

- `DisclosurePackage` 必须包含 `metadata/evidence/sections/figures/questions/audit`；证据主标签只能是 `[F]/[C]/[I]/[A]/[Q]/[L]`。
- `FULL_DISCLOSURE` 至少包含七类核心章节和三张 FigureSpec。正文用 `figure_ref` 回指 `figure_id`，图声明用 `used_by` 回指章节；悬空、重复或无证据引用必须失败。
- `audit.p0` 非空时禁止生成；未有实验、外部检索或结构数据的内容保留 `[Q]/[I]`，不能升级成已验证效果或法律结论。

## 产物与验收

- `figure_output_mode=spec_only` 是模板默认：生成目录包含 `disclosure.md`、`disclosure.docx`、`figure-plan.md` 和 `manifest.json`，不输出或嵌入实际图。`rendered` 才生成 `figures/*.svg`/`*.png` 并将 PNG 嵌入 Word。
- Word 有两个样例保真档位：`sample_exact` 原样复制样例 DOCX；`sample_fidelity` 从样例 donor 复制标题、正文、列表和直接段落格式填充新内容。两者都不引入通用自定义样式。
- validator 要同时检查输入字段、证据回指、图文一一对应、产物文件、DOCX `word/media` 数量和批注缺失；不能只看文件存在。
- validator 还必须拒绝 `figure_id` 越界/绝对路径、symlink、残留输出、manifest hash/bytes 不一致、非法 UTF-8、控制字符、坏节点/边、表格列数不一致和未关闭的 P0；输出目录复用只接受本流水线上一轮的白名单文件。
- `FULL_DISCLOSURE` 的完整章节和 `mode_contract` 是生成门禁；`REWRITE_AUDIT` 的原句/问题/改写必须同时出现在 Markdown、DOCX 和 manifest，不能只在输入校验中存在。正文多证据引用要用 `evidence_primary`，表格要携带证据回指。
- SVG/PNG 图稿必须共享同一 FigureSpec；PNG 箭头按二维方向与 SVG marker 对齐，`sequence` 图使用泳道消息。三类图仅是当前通用最小包，结构图不得从缺失材料臆造部件。
- 需要 AI 视觉底图时，FigureSpec 必须同时声明 `generation_method=imagegen|ppt`、`source_image` 和 `prompt`；底图必须落在项目内，不能只留在 `$CODEX_HOME/generated_images`。模板模式只把这些字段写入 `figure-plan.md`，避免生成模型文字直接成为审计事实。
- Word 有两个保真档位：`sample_fidelity` 用样例 DOCX 的 OOXML/直接格式作为 donor 生成新内容；`sample_exact` 逐字复制样例 DOCX，并用 SHA-256 证明其段落、Unicode 符号和版面基线未被改写。
- `FULL_DISCLOSURE` 图稿必须声明项目内 `source_image`；当前示例底图位于 `.agents/skills/patent-disclosure-distiller/examples/map-preload/source-figures/`。实际图片生成/绘制是独立步骤，交底书模板不携带图片。
- 主回归命令是 `python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v`。示例输入位于 `.agents/skills/patent-disclosure-distiller/examples/map-preload/package.json`。

## 已知边界

- 样例 DOCX 本身有 130 个正文段落、无表格/图形/媒体，且存在手工格式、批注、数值和“结合附图”缺口；它只能提供版式观察，不得直接当模板或事实数据源。
- 当前流水线证明结构化一致性和 DOCX 包媒体关系，不证明所有 Word/WPS 版本的逐页像素等价；代理机构 `.dotx`、PDF 视觉回归、OCR、外部专利检索和效果实验是后续能力。
