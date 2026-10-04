<p align="center">
  <img src=".github/assets/logo.svg" height="96" alt="patent-disclosure-distiller 标志：三滴原料经漏斗蒸馏落入文档">
</p>

# patent-disclosure-distiller

从技术材料、产品设想或现有稿件蒸馏出证据约束的中文专利技术交底书（patent disclosure distiller）

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm--Noncommercial--1.0.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#-快速开始)
[![Tests: 13 unittests](https://img.shields.io/badge/tests-13%20unittests-brightgreen.svg)](.agents/skills/patent-disclosure-distiller/tests)

[English](README.md) | **简体中文**

生成式写作会抹掉一条专利申请承受不起的线：已核实的事实、看似合理的推断与产品宣传，以同一种自信的口吻一起出现。`patent-disclosure-distiller` 是一个把这条线重新画出来的智能体技能。它以「证据约束的技术论证编辑」方式工作——先解释技术关系，再组织专利体例，不把产品宣传、模型名称或法律判断当作技术事实。

底稿里每条关键陈述只携带一个证据标签——`[F]` 是从材料原样取出的事实，`[Q]` 是在证据到位前保持待确认的开放问题。整份底稿像一本记录每条内容来历的实验记录本，只是这本记录本由机器复查：陈述写入 `DisclosurePackage` JSON，Python 流水线据此渲染 Markdown、Word 与附图方案；证据或图文回指撑不住的产物，validator 直接拒绝。适合自己的智能体使用时，把 `.agents/skills/patent-disclosure-distiller/` 整目录复制进技能目录即可。

> [!NOTE]
> 本仓库是私有开发源的公开镜像。镜像发布技能、流水线、评测与蒸馏研究文档，但**不**发布私有样例 DOCX（镜像中无 `sample/` 目录）：三个以它为 Word donor 的测试自动跳过，随包示例的 `disclosure.docx` 仅在提供 donor DOCX 的环境下重新生成（见「把技能复制到其他智能体时」）。

## 目录

- [特性](#-特性)
- [快速开始](#-快速开始)
- [下一步](#-下一步)
- [仓库布局](#-仓库布局)
- [边界声明](#-边界声明)
- [链接](#-链接)
- [贡献](#-贡献)
- [License](#license)

## ✨ 特性

- **证据账本**：每条关键陈述只携带一个主标签——`[F]` 材料事实、`[C]` 本次实际核验、`[I]` 跨材料推导、`[A]` 工作假设、`[Q]` 待确认、`[L]` 法律审查——并写来源定位，未执行的检查明确标注。
- **四种交付模式**：`FULL_DISCLOSURE`＝完整交底书；`TARGETED_SECTION`＝只写指定章节；`REWRITE_AUDIT`＝审计并改写已有稿件；`INTAKE_DRAFT`＝信息不足时的追问式初稿。模式由智能体按用户请求选定并写入 `metadata.delivery_mode`（写法见 `SKILL.md`）——只输出用户要求的内容，不因模板存在就强行凑全文。
- **质量门**：QG-01–QG-14 逐项标记通过/部分/未执行/失败；`audit.p0` 非空时生成器直接拒绝产出。
- **机器校验流水线**：validator 拒绝悬空图文回指、缺失证据引用、DOCX 媒体数量不一致、残留文件和 manifest hash/字节数不一致。
- **样例保真 Word 输出**：`sample_exact` 逐字节复制样例 DOCX（SHA-256 证明）；`sample_fidelity` 以样例直接段落格式为 donor 填充新内容。
- **仅方案附图**：技能模板与示例包默认 `figure_output_mode=spec_only`，输出附图方案（节点、边、图题、提示词、项目内底图路径），不嵌入实际图片；自写 package 未声明该字段时，流水线按 `rendered` 回退处理。

## 🔨 快速开始

本技能面向支持 SKILL.md 约定（YAML frontmatter 的 `name`/`description`）的智能体运行时：复制进技能目录后，智能体按 `description` 自动触发（触发行为已由 [evals/](evals/) 的 description-only 独立测试验证）。不依赖智能体时，也可直接用 `scripts/` 下的 validate/generate 脚本手动驱动流水线。以下命令均在仓库根目录执行（示例路径均为相对路径）：

```bash
cd patent-disclosure-distiller
```

需要 Python 3.9+（3.9 实测）并安装 Pillow 与 python-docx。建议用虚拟环境安装（macOS Homebrew Python 等外部管理环境下 `pip3` 直装会被拒绝）：

```bash
python3 -m venv .venv && source .venv/bin/activate && pip3 install pillow python-docx
```

校验示例输入：

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json
# VALID: .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json
```

生成产物——目录内得到 `disclosure.md`、`disclosure.docx`、`figure-plan.md`、`manifest.json` 共 4 个文件；下方输出里的 `files` 不计入 `manifest.json`（口径见 pipeline.py 的 manifest 构建逻辑），所以是 3：

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/generate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json \
  /tmp/disclosure-output
# {"output": "/tmp/disclosure-output", "files": 3, "figures": 3}
```

示例命令为 Unix shell 写法；Windows 下请把 `/tmp/disclosure-output` 换成本地可写目录（如 `%TEMP%\\disclosure-output`）。

校验生成产物：

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py /tmp/disclosure-output
# VALID: /tmp/disclosure-output
```

跑回归测试：

```bash
python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v
# Ran 13 tests ... OK（公开镜像中 10 项：3 个样例 donor 测试跳过）
```

### 把技能复制到其他智能体时

随包示例使用 `sample_exact` 档位并回指样例 DOCX（私有开发源中的 `sample/`，公开镜像不含）。技能目录复制出去后，写作规则与校验不受影响；重新生成该示例需任选其一（样例 DOCX 不随技能目录分发）：

1. `generate_disclosure.py` 加 `--reference-docx <某个可作为版式 donor 的 .docx 路径>`；
2. 把 package.json 的 `metadata.reference_docx` 改指向你自己的 donor DOCX；
3. 改用其他 `docx_profile` 档位——`native`（不依赖 donor，缺省默认）、`sample_fidelity`（以 donor 的页面/段落直接格式生成新内容）、`sample_exact`（逐字复制 donor）；各档位对 donor 的要求见 `references/pipeline.md`。

## 🚀 下一步

用你自己的材料开始：

1. 按 `references/template.md` 的字段模板（或复制 `examples/map-preload/package.json` 改写）构建 `DisclosurePackage` JSON；
2. 先跑 `scripts/validate_disclosure.py` 校验输入；
3. 再跑 `scripts/generate_disclosure.py` 生成产物，并对输出目录重新校验；
4. 交付模式与证据标签的写法见 `SKILL.md` 与 `references/methodology.md`。

## 📦 仓库布局

| 路径 | 内容 |
|---|---|
| [`.agents/skills/patent-disclosure-distiller/`](.agents/skills/patent-disclosure-distiller/) | 技能本体：写作规则（`SKILL.md` + `references/`）、`DisclosurePackage` schema、校验/生成/流水线脚本、示例包、unittest 套件 |
| [`distillation/`](distillation/) | 从一份私有样例交底书蒸馏写作模型的研究文档；规则的证据来源，不是运行时代码。样例 DOCX 本体、其解包提取目录与逐字引用型证据文档（`sample-evidence.md`、`word-level-method.md`）仅保留在私有开发源 |
| [`evals/`](evals/) | 技能评测：description-only 触发判断测试（`trigger-test.md`），软件/机械/流程等多条技术路线的场景响应行为评测（`software.md`、`mechanical.md`、`process.md`、`process-with-source.md`），QG-01–QG-14 盲评复核的完整交底书实质评测（`full-mechanical.md`），以及可执行的流水线冒烟评测脚本 `run_pipeline_eval.py` |
| `.spec/docs/` | spec 工作流沉淀的工程事实文档与审计处置记录（仅私有开发源，不随镜像发布） |

## 🧱 边界声明

> [!WARNING]
> - 技能产出的是技术写作底稿，不替代专利检索、代理师判断或法务意见，也不据此断言新颖性或创造性。
> - 效果声明受证据约束：没有实验、外部检索或结构数据的内容保持 `[Q]`/`[I]`，不会升级为已验证结论；`audit.p0` 非空时禁止生成。
> - Word 保真是结构性的：流水线证明包结构、媒体关系和 hash 一致——不证明所有 Word/WPS 版本的逐页像素等价。代理机构 `.dotx` 模板、PDF 视觉回归和 OCR 是后续能力，不是当前功能。

## 🔗 链接

- [SKILL.md](.agents/skills/patent-disclosure-distiller/SKILL.md) — 技能入口、交付模式、证据标签
- [references/pipeline.md](.agents/skills/patent-disclosure-distiller/references/pipeline.md) — 输入契约、命令、manifest 与验收
- [references/methodology.md](.agents/skills/patent-disclosure-distiller/references/methodology.md) — 技术路线、单一证据标签、十三步转换算法
- [references/template.md](.agents/skills/patent-disclosure-distiller/references/template.md) — 完整交底书字段模板
- [references/quality-gates.md](.agents/skills/patent-disclosure-distiller/references/quality-gates.md) — QG-01–QG-14、P0/P1/P2、发布级别
- [references/domain-adaptation.md](.agents/skills/patent-disclosure-distiller/references/domain-adaptation.md) — 输入形态分支、跨领域适配卡、追问优先级协议（四种交付模式见 [SKILL.md](.agents/skills/patent-disclosure-distiller/SKILL.md) 与 [references/template.md](.agents/skills/patent-disclosure-distiller/references/template.md)）
- [examples/map-preload/](.agents/skills/patent-disclosure-distiller/examples/map-preload/) — 可复现的 `FULL_DISCLOSURE` 示例（[README](.agents/skills/patent-disclosure-distiller/examples/map-preload/README.md)）

## 🤝 贡献

本仓库是私有开发源的公开镜像；内部工作流程在开发源进行。在仓库内工作请先读 [AGENTS.md](AGENTS.md)（分层、数据契约与验收规则），让 `sample/` 与 `distillation/` 保持各自文档声明的角色；提交前按 [CONTRIBUTING.md](CONTRIBUTING.md) 的清单自查，其中包括每次改动都必须通过回归测试。行为准则见 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)；安全问题报告方式见 [SECURITY.md](SECURITY.md)。

## License

[PolyForm Noncommercial 1.0.0](LICENSE) © 2026 mxk。禁止商业使用；个人使用、研究、教育与公益用途欢迎使用。开发真源保持在私有远端 `git.mxk.dev`；任何公开发布都是独立的筛选链路，并携带本许可。本文件中文版与英文版 [README.md](README.md) 结构一致，如有出入以英文版为准。
