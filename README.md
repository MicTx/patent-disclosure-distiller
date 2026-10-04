<p align="center">
  <img src=".github/assets/logo.svg" height="96" alt="patent-disclosure-distiller logo: three drops distilled through a funnel into a document">
</p>

# patent-disclosure-distiller

Distills evidence-constrained Chinese patent disclosures from technical material, product ideas, or existing drafts

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm--Noncommercial--1.0.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#-quick-start)
[![Tests: 13 unittests](https://img.shields.io/badge/tests-13%20unittests-brightgreen.svg)](.agents/skills/patent-disclosure-distiller/tests)

**English** | [简体中文](README.zh-CN.md)

Generative writing blurs a line that a patent filing cannot afford to lose: verified facts, plausible inferences, and product marketing arrive in the same confident voice. `patent-disclosure-distiller` is an agent skill that redraws it. It works as an evidence-constrained technical-argument editor — explain the technical relations first, organize them into patent format second, and never pass product marketing, model names, or legal judgement off as technical fact.

Every key statement in a draft carries exactly one evidence label — from `[F]` for facts taken straight from your material to `[Q]` for open questions that stay questions until evidence arrives. The draft works like a lab notebook that records where each entry came from, except this notebook is machine-checked: statements go into a `DisclosurePackage` JSON, a Python pipeline renders Markdown, Word, and figure plans from it, and the validator refuses output whose evidence or figure references have nothing behind them. To use the skill in your own agent, copy `.agents/skills/patent-disclosure-distiller/` into its skills directory.

> [!NOTE]
> This repository is the public mirror of a private development source. The mirror publishes the skill, the pipeline, the evals and the distillation research notes, but **not** the private sample DOCX (`sample/` is absent): three tests that use it as a Word donor skip automatically, and the bundled example regenerates its `disclosure.docx` only where a donor DOCX is supplied (see [Copying the skill into another agent](#copying-the-skill-into-another-agent)).

## Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Next steps](#-next-steps)
- [Repository Layout](#-repository-layout)
- [Boundaries](#-boundaries)
- [Links](#-links)
- [Contributing](#-contributing)
- [License](#license)

## ✨ Features

- **Evidence ledger**: every key statement carries exactly one primary label — `[F]` material fact, `[C]` verified this run, `[I]` inference, `[A]` working assumption, `[Q]` open question, `[L]` legal review — each with a source anchor or an explicit "not executed".
- **Four delivery modes**: `FULL_DISCLOSURE` = the complete disclosure; `TARGETED_SECTION` = only the requested sections; `REWRITE_AUDIT` = audit and rewrite an existing draft; `INTAKE_DRAFT` = a question-driven skeleton when material is thin. The agent picks the mode from the user's request and writes it into `metadata.delivery_mode` (see `SKILL.md`) — output covers exactly what was asked, never padded to the full template.
- **Quality gates**: QG-01–QG-14 are marked passed / partial / not run / failed; a non-empty `audit.p0` makes the generator refuse to produce anything.
- **Machine-checked pipeline**: the validator rejects dangling figure references, missing evidence back-references, DOCX media-count mismatches, leftover files, and manifest hash/bytes mismatches.
- **Sample-faithful Word output**: `sample_exact` byte-copies the sample DOCX (SHA-256 proven); `sample_fidelity` reuses its direct paragraph formatting as a donor for new content.
- **Spec-only figures**: the skill template and example package default to `figure_output_mode=spec_only`, emitting figure plans (nodes, edges, captions, prompts, in-project base images) without embedding rendered images; when a hand-written package omits the field, the pipeline falls back to `rendered`.

## 🔨 Quick Start

This skill targets agent runtimes that support the SKILL.md convention (YAML frontmatter `name`/`description`): once copied into the skills directory, the agent triggers it automatically off the `description` (trigger behavior is verified by the description-only independent tests under [evals/](evals/)). Without an agent, you can also drive the pipeline manually with the validate/generate scripts under `scripts/`. All commands below run from the repository root (example paths are relative):

```bash
cd patent-disclosure-distiller
```

Requires Python 3.9+ (tested on 3.9) with Pillow and python-docx. Installing inside a virtual environment is recommended (bare `pip3` installs are refused on externally managed Pythons such as Homebrew's on macOS):

```bash
python3 -m venv .venv && source .venv/bin/activate && pip3 install pillow python-docx
```

Validate the example input:

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json
# VALID: .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json
```

Generate artifacts — the output directory holds four files: `disclosure.md`, `disclosure.docx`, `figure-plan.md`, `manifest.json`; the `files` field in the output below does not count `manifest.json` (per the manifest-building logic in pipeline.py), hence 3:

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/generate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json \
  /tmp/disclosure-output
# {"output": "/tmp/disclosure-output", "files": 3, "figures": 3}
```

The example commands assume a Unix shell; on Windows, replace `/tmp/disclosure-output` with a locally writable directory (e.g. `%TEMP%\\disclosure-output`).

Validate the generated output:

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py /tmp/disclosure-output
# VALID: /tmp/disclosure-output
```

Run the regression suite:

```bash
python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v
# Ran 13 tests ... OK (10 in the public mirror: 3 sample-donor tests skip)
```

### Copying the skill into another agent

The bundled example uses the `sample_exact` profile and points at the sample DOCX (`sample/` in the private development source; absent from this mirror). Once the skill directory is copied elsewhere, the writing rules and validation are unaffected; regenerating that example requires one of the following (the sample DOCX is not distributed with the skill directory):

1. Pass `--reference-docx <path to a .docx usable as a layout donor>` to `generate_disclosure.py`;
2. Point `metadata.reference_docx` in your package.json at your own donor DOCX;
3. Switch to another `docx_profile` tier — `native` (no donor needed, the default), `sample_fidelity` (builds new content from the donor's page/direct-paragraph formatting), `sample_exact` (byte-copies the donor); donor requirements per tier are documented in `references/pipeline.md`.

## 🚀 Next steps

Start with your own material:

1. Build a `DisclosurePackage` JSON from the field template in `references/template.md` (or copy and adapt `examples/map-preload/package.json`);
2. Validate the input first with `scripts/validate_disclosure.py`;
3. Generate artifacts with `scripts/generate_disclosure.py`, then re-validate the output directory;
4. For delivery modes and evidence-label writing rules, see `SKILL.md` and `references/methodology.md`.

## 📦 Repository Layout

| Path | What it holds |
|---|---|
| [`.agents/skills/patent-disclosure-distiller/`](.agents/skills/patent-disclosure-distiller/) | The skill: writing rules (`SKILL.md` + `references/`), `DisclosurePackage` schema, validate/generate/pipeline scripts, example package, unittest suite |
| [`distillation/`](distillation/) | Research notes distilling the writing model from a private sample disclosure; evidence for the rules, not runtime code. The sample DOCX itself, its extracted workdir, and the verbatim-quote evidence files (`sample-evidence.md`, `word-level-method.md`) stay in the private development source |
| [`evals/`](evals/) | Skill evaluation: description-only trigger tests against distractor skills (`trigger-test.md`), behavior/response evals for targeted-section scenarios across software / mechanical / process routes (`software.md`, `mechanical.md`, `process.md`, `process-with-source.md`), a QG-01–QG-14 blind-reviewed output audit of a full disclosure (`full-mechanical.md`), and an executable pipeline smoke eval (`run_pipeline_eval.py`) |
| `.spec/docs/` | Engineering-facts documents and audit dispositions from the spec workflow (private development source only; not published in this mirror) |

## 🧱 Boundaries

> [!WARNING]
> - The skill writes technical drafts. It does not replace patent search, patent-attorney judgement, or legal review, and it does not assert novelty or inventive step.
> - Effect claims stay evidence-bound: without experiments, external search, or structural data, content keeps `[Q]`/`[I]` and is never upgraded to verified results; a non-empty `audit.p0` blocks generation.
> - Word fidelity is structural: the pipeline proves package, media, and hash consistency — not pixel-identical pagination in every Word/WPS version. Agency `.dotx` templates, PDF visual regression, and OCR are future capabilities, not current features.

## 🔗 Links

- [SKILL.md](.agents/skills/patent-disclosure-distiller/SKILL.md) — skill entry point, delivery modes, evidence labels
- [references/pipeline.md](.agents/skills/patent-disclosure-distiller/references/pipeline.md) — input contract, commands, manifest and acceptance
- [references/methodology.md](.agents/skills/patent-disclosure-distiller/references/methodology.md) — technical routes, single-label evidence, 13-step algorithm
- [references/template.md](.agents/skills/patent-disclosure-distiller/references/template.md) — full disclosure field template
- [references/quality-gates.md](.agents/skills/patent-disclosure-distiller/references/quality-gates.md) — QG-01–QG-14, P0/P1/P2, release levels
- [references/domain-adaptation.md](.agents/skills/patent-disclosure-distiller/references/domain-adaptation.md) — input-shape branches, cross-domain adaptation cards, question-priority protocol (the four delivery modes are defined in [SKILL.md](.agents/skills/patent-disclosure-distiller/SKILL.md) and [references/template.md](.agents/skills/patent-disclosure-distiller/references/template.md))
- [examples/map-preload/](.agents/skills/patent-disclosure-distiller/examples/map-preload/) — reproducible `FULL_DISCLOSURE` example ([README](.agents/skills/patent-disclosure-distiller/examples/map-preload/README.md))

## 🤝 Contributing

This repository is the public mirror of a private development source; internal workflow happens there. To work in the repository itself, read [AGENTS.md](AGENTS.md) first (layering, data contract, acceptance rules), keep `sample/` and `distillation/` within their documented roles, and follow the checklist in [CONTRIBUTING.md](CONTRIBUTING.md) — it names the regression command every change must pass. For conduct expectations see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md); to report a security issue follow [SECURITY.md](SECURITY.md).

## License

[PolyForm Noncommercial 1.0.0](LICENSE) © 2026 mxk. Commercial use is not permitted; personal, research, educational, and nonprofit use is welcome. The development source of truth stays on the private remote `git.mxk.dev`; any public release is a separate, filtered pipeline that carries this license.
