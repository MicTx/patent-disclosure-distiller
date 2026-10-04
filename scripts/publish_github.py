#!/usr/bin/env python3
"""发布门禁脚本：把私有开发源的可公开子集发布为 GitHub 镜像。

用法:
    python3 scripts/publish_github.py --dry-run   # 构建导出态 + 全部机器验收，不推送
    python3 scripts/publish_github.py            # 验收通过后：orphan 单提交 + force-push + 设为公开

发布边界（由用户 2026-10-04 决策）:
    - sample/ 的原始 DOCX 不公开；其「内容化身」同样剥离：
      * examples/map-preload/output/（disclosure.docx 是样例的逐字节副本）
      * distillation/workdir/（样例 DOCX 的完整解包提取，含 130 段逐字正文）
      * .spec/（内部工程过程记录，含 retired 提取脚本）
    - distillation/ 的 7 份研究 md、evals/、技能本体与流水线公开。

安全设计:
    - 导出态从 git ls-files 构建（不含未跟踪文件），白名单式排除；
    - 验收失败即退出非零，绝不推送；
    - 历史是 orphan 单提交：公开仓不携带任何私有 blob 的历史。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "patent-disclosure-distiller"

# 排除规则：任何命中（目录前缀或文件路径）都不进入导出态。
EXCLUDE_PREFIXES = (
    "sample/",
    ".spec/",
    ".zcode/",
    "distillation/workdir/",
    "distillation/sample-evidence.md",
    "distillation/word-level-method.md",
    ".agents/skills/patent-disclosure-distiller/examples/map-preload/output/",
    "docs/",
)
# .spec 下的 retired 提取脚本路径（若用户改为发布 .spec 时单独处理）


def run(cmd: list[str], cwd: Path | None = None, check: bool = True,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if check and proc.returncode != 0:
        raise SystemExit(f"命令失败 {' '.join(cmd)}\n{proc.stdout}\n{proc.stderr}")
    return proc


def export_tree(dest: Path) -> list[str]:
    """按 git ls-files 把可公开子集复制到 dest，返回相对路径清单。"""
    tracked = run(["git", "ls-files", "-z"], cwd=ROOT).stdout.split("\0")
    exported: list[str] = []
    for rel in tracked:
        if not rel:
            continue
        if any(rel.startswith(p) or rel == p.rstrip("/") for p in EXCLUDE_PREFIXES):
            continue
        if rel.endswith(".DS_Store"):
            continue
        src = ROOT / rel
        if not src.is_file():
            raise SystemExit(f"git 索引中的文件缺失: {rel}")
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        exported.append(rel)
    return exported


def check_no_sample_blob(exported: list[str]) -> None:
    """验收 1：样例 DOCX 的 SHA-256 不得出现在任何导出文件中。"""
    sample_sha = hashlib.sha256(
        (ROOT / "sample" / "一种基于马尔可夫链的地图瓦片及范围数据预加载方法.docx").read_bytes()
    ).hexdigest()
    for rel in exported:
        if rel.endswith((".docx", ".zip", ".png")):
            data = (Path(rel)).read_bytes()
        else:
            data = Path(rel).read_bytes()
        if sample_sha.encode() in data:
            raise SystemExit(f"样例 blob SHA 出现在导出文件 {rel}")
    # 样例 DOCX 文件本体不出现
    if any(rel.startswith("sample/") for rel in exported):
        raise SystemExit("导出态包含 sample/ 路径")


def check_regression(dest: Path) -> int:
    """验收 2：公开导出态的回归测试（11 项应过、2 项 donor 跳过）。"""
    import os
    loader = unittest.TestLoader()
    sys.path.insert(0, str(dest / ".agents" / "skills" / "patent-disclosure-distiller" / "scripts"))
    tests_dir = dest / ".agents" / "skills" / "patent-disclosure-distiller" / "tests"
    suite = loader.discover(str(tests_dir))
    with open(os.devnull, "w") as sink:
        runner = unittest.TextTestRunner(verbosity=2, stream=sink)
        result = runner.run(suite)
    ran = result.testsRun
    skipped = len(result.skipped)
    failures = len(result.failures) + len(result.errors)
    if failures:
        for test, tb in result.failures + result.errors:
            print(f"FAIL: {test}\n{tb}", file=sys.stderr)
        raise SystemExit(f"导出态回归失败：{failures} 个失败")
    if ran != 13 or skipped != 3:
        raise SystemExit(f"导出态测试数量异常：ran={ran} skipped={skipped}（期望 13 跑、10 过 + 3 个 donor 测试跳过）")
    return ran - skipped


def check_example_pipeline(dest: Path) -> None:
    """验收 3：示例输入校验通过；无 donor 时 sample_exact 生成按契约拒绝（fail-closed）。

    必须在以 dest 为 cwd 的子进程里跑：_find_reference_docx 的候选路径含 Path.cwd()，
    在私有仓库根目录跑会用私有 sample/ 命中 donor，测不出镜像态行为。
    """
    probe = (
        "import sys, tempfile\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(dest / '.agents' / 'skills' / 'patent-disclosure-distiller' / 'scripts')!r})\n"
        "from pipeline import load_json, validate_package, render_package, PackageValidationError\n"
        f"fixture = Path({str(dest / '.agents' / 'skills' / 'patent-disclosure-distiller' / 'examples' / 'map-preload' / 'package.json')!r})\n"
        "data = load_json(fixture)\n"
        "errs = validate_package(data)\n"
        "assert not errs, f'validate failed: {errs}'\n"
        "with tempfile.TemporaryDirectory() as tmp:\n"
        "    try:\n"
        "        render_package(fixture, Path(tmp))\n"
        "    except PackageValidationError as exc:\n"
        "        assert '找不到 reference_docx' in str(exc), f'unexpected error: {exc}'\n"
        "    else:\n"
        "        raise AssertionError('render succeeded without donor — fixture must not resolve a donor in the mirror')\n"
        "print('probe-ok')\n"
    )
    proc = subprocess.run([sys.executable, "-c", probe], cwd=dest, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"导出态示例 fail-closed 检查失败:\n{proc.stdout}\n{proc.stderr}")


def check_readme_audit(dest: Path) -> None:
    """验收 4：两版 README 相对链接在导出态内全部有效；audit.py 无 error。"""
    audit = Path("/Users/dawud/.agents/skills/readme-skill/scripts/audit.py")
    for name, desc in [
        ("README.md", "Distills evidence-constrained Chinese patent disclosures from technical material, product ideas, or existing drafts"),
        ("README.zh-CN.md", "Distills evidence-constrained Chinese patent disclosures from technical material, product ideas, or existing drafts"),
    ]:
        proc = subprocess.run(
            [sys.executable, str(audit), name, "--desc", desc, "--root", str(dest)],
            cwd=dest, capture_output=True, text=True,
        )
        report = json.loads(proc.stdout)
        if report["errors"]:
            raise SystemExit(f"{name} audit error: {report['errors']}")
    # 相对链接存在性（audit --root 已覆盖，此处双保险：手工核对 sample/ 死链）
    for name in ("README.md", "README.zh-CN.md", "CONTRIBUTING.md"):
        text = (dest / name).read_text(encoding="utf-8")
        for target in re.findall(r"\]\((?!https?:|mailto:|#)([^)#]+)(?:#[^)]*)?\)", text):
            if not (dest / target.strip()).exists():
                raise SystemExit(f"{name} 相对链接在导出态中缺失: {target}")


def check_no_private_markers(dest: Path, exported: list[str]) -> None:
    """验收 5：样例正文文本不逐字出现在导出态的任何文件中（标题已在公开蒸馏文档中按用户决策保留）。"""
    tsv = ROOT / "distillation" / "workdir" / "_docx_work" / "paragraphs.tsv"
    sample_paragraphs = []
    for line in tsv.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 6:
            text = parts[-1].strip()
            # 长句才做泄漏判定（>30 字的正文句），短词如「技术领域」是通用术语
            if len(text) >= 30:
                sample_paragraphs.append(text)
    leaked = []
    for rel in exported:
        p = dest / rel
        if p.suffix.lower() in {".docx", ".png", ".zip"}:
            continue
        try:
            content = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for para in sample_paragraphs:
            if para in content:
                leaked.append((rel, para[:50]))
    if leaked:
        for rel, frag in leaked[:5]:
            print(f"LEAK: {rel} 含样例正文片段: {frag}...", file=sys.stderr)
        raise SystemExit(f"导出态发现 {len(leaked)} 处样例逐字正文泄漏")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只构建导出态并验收，不推送")
    parser.add_argument("--remote", default="github", help="GitHub remote 名")
    parser.add_argument("--branch", default="main", help="推送分支名")
    args = parser.parse_args()

    # 构建导出态
    tmpdir = Path(tempfile.mkdtemp(prefix="ptw-publish-"))
    dest = tmpdir / "export"
    try:
        exported = export_tree(dest)
        print(f"导出态：{len(exported)} 个文件")

        check_no_sample_blob(exported)
        print("验收 1 通过：无样例 blob/路径")
        n = check_regression(dest)
        print(f"验收 2 通过：导出态回归 {n} 项过、3 项 donor 跳过")
        check_example_pipeline(dest)
        print("验收 3 通过：示例 fail-closed 行为符合契约")
        check_readme_audit(dest)
        print("验收 4 通过：README audit + 链接有效")
        check_no_private_markers(dest, exported)
        print("验收 5 通过：无样例逐字正文泄漏")

        if args.dry_run:
            print("DRY-RUN 完成：导出态自洽，未推送。")
            return 0

        # 构造孤立单提交：临时索引 + commit-tree，不触碰工作区与当前分支
        import os
        index_file = tmpdir / "publish-index"
        env_index = {**os.environ, "GIT_INDEX_FILE": str(index_file)}
        run(["git", "read-tree", "--empty"], env=env_index)
        for rel in exported:
            blob = subprocess.run(
                ["git", "hash-object", "-w", "--", str(dest / rel)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip()
            run(["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}"],
                env=env_index)
        tree = subprocess.run(
            ["git", "write-tree"], cwd=ROOT, capture_output=True, text=True, check=True,
            env=env_index,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "commit-tree", tree, "-m",
             "publish: public mirror of patent-disclosure-distiller (sample excluded)\n\n"
             "Filtered from the private development source: sample DOCX, its byte-copy\n"
             "example output, the distillation workdir extraction and verbatim-quote\n"
             "evidence files, and internal .spec records are excluded; skill, pipeline,\n"
             "evals, and analytical distillation notes are included."],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        print(f"orphan 提交: {commit}")
        run(["git", "push", "--force", args.remote, f"{commit}:refs/heads/{args.branch}"])
        print(f"已 force-push {commit} -> {args.remote}/{args.branch}（孤立历史，不含私有 blob）")

        # 设为公开
        proc = subprocess.run(["gh", "repo", "edit", "MicTx/patent-disclosure-distiller", "--visibility", "public", "--accept-visibility-change-consequences"],
                               capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"警告：切换公开失败，请手动执行 gh repo edit --visibility public\n{proc.stderr}", file=sys.stderr)
        else:
            print("GitHub 仓库已设为 public")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    devnull = subprocess.DEVNULL
    raise SystemExit(main())
