# 贡献指南（内部项目）

本仓库是私有开发源（git.mxk.dev）上的内部项目，没有外部贡献流程；本文面向在仓库内工作的协作者。
对外发布走另一条链路：GitHub 公开仓只接收经过筛选、清理和发布门禁的提交，与开发真源分开维护。

## From the public mirror (GitHub)

Development happens in the private source repository and is republished here as a filtered snapshot: each publish rebuilds the mirror as a single commit, so pull requests cannot be merged and commits made on the mirror do not persist. If something in the published skill, pipeline, or docs looks wrong:

1. Open an issue (bug template) describing the failure and the mirror commit you are running;
2. For security reports or unpublished invention material, follow [SECURITY.md](SECURITY.md) instead — never paste such material into an issue;
3. Usage questions and ideas go to [Discussions](https://github.com/MicTx/patent-disclosure-distiller/discussions).

Fixes are ported by the maintainer and appear here with the next publish.

## 仓库事实优先

动手前先读 [AGENTS.md](AGENTS.md)：分层与入口、`DisclosurePackage` 数据契约、产物验收规则和已知边界都在那里。
两条硬边界对任何改动都成立：

- `sample/` 的原始 DOCX 是只读基线（仅私有开发源中存在），不提交对它的任何修改。
- [`distillation/`](distillation/) 是研究文档，不是运行时代码；不要把它的散文当字段真源。

## 改动自查清单

提交前逐项确认：

1. **主回归通过**：`python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v` 必须全绿
   （13 项测试覆盖正负样本与 DOCX 包检查）。
2. **流水线端到端可复现**：`validate → generate → validate` 三步对
   `examples/map-preload/package.json` 仍然依次输出 `VALID`。
3. **schema 与文档同步**：改了 `schemas/disclosure-package.schema.json` 或
   `scripts/pipeline.py` 的行为时，同步更新 `references/pipeline.md`；行为不变时不改文档。
4. **不引入通用自定义样式**：Word 两档保真（`sample_exact`/`sample_fidelity`）都不引入
   通用自定义样式，改动 renderer 时保持这一点。
5. **示例产物再生成**：动了示例输入或生成逻辑时，重新生成
   `examples/map-preload/output/` 并确认 manifest hash 一致。
6. **证据纪律**：正文叙述不得声称未验证的效果、法律结论或实验结果；
   保持 `[Q]/[I]` 的内容保持 `[Q]/[I]`。

## 提交约定

- commit message 跟随仓库现有风格（`feat(scope):`、`fix(scope):`、`chore(scope):`、`docs:`）。
- spec 工作流的处置记录归档到 `.spec/`；审计遗留关注项关闭前不合并。
- 涉及 `.agents/skills/patent-disclosure-distiller/` 的技能行为变更，需在 `evals/` 有对应评测
   佐证（触发测试或场景行为评测）。
