from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
import shutil
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pipeline import (  # noqa: E402
    PackageValidationError,
    load_json,
    render_package,
    validate_outputs,
    validate_package,
)


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "map-preload" / "package.json"
SAMPLE_DOCX = Path(__file__).resolve().parents[4] / "sample" / "一种基于马尔可夫链的地图瓦片及范围数据预加载方法.docx"


@unittest.skipUnless(SAMPLE_DOCX.is_file(), "sample DOCX donor only exists in the private development repo")
class SampleDonorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_json(FIXTURE)

    def test_render_and_validate_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = render_package(FIXTURE, output)
            self.assertEqual(len(manifest["figures"]), 3)
            self.assertTrue(all(figure["render_mode"] == "spec_only" for figure in manifest["figures"]))
            self.assertTrue((output / "figure-plan.md").is_file())
            self.assertEqual(validate_outputs(output), [])
            self.assertTrue((output / "disclosure.md").read_text(encoding="utf-8").count("fig-") >= 3)
            with zipfile.ZipFile(output / "disclosure.docx") as archive:
                media = [name for name in archive.namelist() if name.startswith("word/media/")]
                self.assertEqual(len(media), 0)
                self.assertIn("word/comments.xml", archive.namelist())
            markdown = (output / "disclosure.md").read_text(encoding="utf-8")
            self.assertIn("主题与摘要", markdown)
            self.assertIn("[I]", markdown)
            self.assertIn("表格证据： [F] [I]", markdown)

    def test_sample_exact_reproduces_reference_docx(self) -> None:
        package = copy.deepcopy(self.data)
        package["metadata"]["docx_profile"] = "sample_exact"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = root / "package.json"
            shutil.copytree(FIXTURE.parent / "source-figures", root / "source-figures")
            package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
            output = root / "output"
            render_package(package_path, output, reference_docx=SAMPLE_DOCX)
            self.assertEqual(hashlib.sha256((output / "disclosure.docx").read_bytes()).hexdigest(), hashlib.sha256(SAMPLE_DOCX.read_bytes()).hexdigest())
            self.assertEqual(validate_outputs(output), [])

    def test_sample_fidelity_fills_content_without_embedding_figures(self) -> None:
        package = copy.deepcopy(self.data)
        package["metadata"]["docx_profile"] = "sample_fidelity"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = root / "package.json"
            package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
            shutil.copytree(FIXTURE.parent / "source-figures", root / "source-figures")
            output = root / "output"
            render_package(package_path, output, reference_docx=SAMPLE_DOCX)
            self.assertNotEqual(hashlib.sha256((output / "disclosure.docx").read_bytes()).hexdigest(), hashlib.sha256(SAMPLE_DOCX.read_bytes()).hexdigest())
            self.assertEqual(validate_outputs(output), [])
            with zipfile.ZipFile(output / "disclosure.docx") as archive:
                self.assertEqual([name for name in archive.namelist() if name.startswith("word/media/")], [])


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_json(FIXTURE)

    def test_fixture_is_valid(self) -> None:
        self.assertEqual(validate_package(self.data), [])

    def test_full_package_requires_figures_and_core_sections(self) -> None:
        broken = copy.deepcopy(self.data)
        broken["figures"] = broken["figures"][:2]
        broken["sections"] = [section for section in broken["sections"] if section["id"] != "effects"]
        errors = validate_package(broken)
        self.assertTrue(any("至少需要 3 张" in error for error in errors))
        self.assertTrue(any("缺少章节" in error for error in errors))

    def test_missing_evidence_and_figure_are_rejected(self) -> None:
        broken = copy.deepcopy(self.data)
        broken["sections"][0]["blocks"][0].pop("evidence")
        for section in broken["sections"]:
            for block in section["blocks"]:
                if block.get("type") == "figure_ref":
                    block["figure_id"] = "fig-missing"
                    break
            else:
                continue
            break
        errors = validate_package(broken)
        self.assertTrue(any("必须声明 evidence" in error for error in errors))
        self.assertTrue(any("不存在附图" in error for error in errors))

    def test_p0_audit_blocks_rendering(self) -> None:
        broken = copy.deepcopy(self.data)
        broken["audit"]["p0"] = ["missing figure"]
        errors = validate_package(broken)
        self.assertIn("audit.p0 非空，存在未关闭的阻断问题", errors)

    def test_manifest_content_is_stable_for_same_input(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_manifest = render_package(FIXTURE, Path(first))
            second_manifest = render_package(FIXTURE, Path(second))
            self.assertEqual(first_manifest["input_sha256"], second_manifest["input_sha256"])
            self.assertEqual(first_manifest["sections"], second_manifest["sections"])
            self.assertEqual(first_manifest["figures"], second_manifest["figures"])
            self.assertEqual(first_manifest["evidence_summary"], second_manifest["evidence_summary"])
            self.assertEqual(first_manifest, second_manifest)

    def test_invalid_path_and_malformed_types_fail_closed(self) -> None:
        broken = copy.deepcopy(self.data)
        broken["metadata"]["delivery_mode"] = []
        broken["sections"][0]["blocks"][0]["evidence"] = [{}]
        broken["figures"][0]["id"] = "fig-../../escape"
        errors = validate_package(broken)
        self.assertTrue(any("delivery_mode" in error for error in errors))
        self.assertTrue(any("evidence" in error for error in errors))
        self.assertTrue(any("未被正文" in error or "figure.id" in error for error in errors))

    def test_control_char_and_graph_edges_are_rejected(self) -> None:
        broken = copy.deepcopy(self.data)
        broken["metadata"]["title"] = "坏\x00标题"
        broken["figures"][0]["edges"] = [{"from": "input", "to": "missing"}]
        errors = validate_package(broken)
        self.assertTrue(any("metadata.title" in error for error in errors))
        self.assertTrue(any("不存在节点" in error for error in errors))

    def test_malformed_nested_values_never_raise(self) -> None:
        mutations = [
            lambda value: value["evidence"].__getitem__(0).update({"type": []}),
            lambda value: value["evidence"].__getitem__(0).update({"id": []}),
            lambda value: value["sections"][0]["blocks"][0].update({"evidence": 1}),
            lambda value: value["sections"][0]["blocks"][0].update({"evidence_primary": []}),
            lambda value: value["figures"][0].update({"used_by": 1}),
            lambda value: value["figures"][0].update({"evidence": 1}),
        ]
        for mutate in mutations:
            broken = copy.deepcopy(self.data)
            mutate(broken)
            self.assertIsInstance(validate_package(broken), list)

    def test_output_validator_catches_deleted_figure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_package(FIXTURE, output)
            (output / "figure-plan.md").unlink()
            errors = validate_outputs(output)
            self.assertTrue(any("figure-plan.md" in error or "附图方案" in error for error in errors))

    def test_output_validator_catches_manifest_tamper_and_stale_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_package(FIXTURE, output)
            (output / "disclosure.md").write_text("tampered", encoding="utf-8")
            errors = validate_outputs(output)
            self.assertTrue(any("SHA-256" in error for error in errors))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_package(FIXTURE, output)
            (output / "orphan.txt").write_text("stale", encoding="utf-8")
            with self.assertRaises(PackageValidationError):
                render_package(FIXTURE, output)


if __name__ == "__main__":
    unittest.main()
