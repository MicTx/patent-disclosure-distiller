# 地图数据预加载示例包

`package.json` 是一个完整的 `FULL_DISCLOSURE` 输入示例。它刻意把空间坐标、缓存并发、更新公式和效果实验保留为 `[Q]`，因此输出状态是“受限底稿”，不会把样例中的宣传性数字当成验证结果。

生成：

```bash
python3 .agents/skills/patent-disclosure-distiller/scripts/generate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/package.json \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/output
python3 .agents/skills/patent-disclosure-distiller/scripts/validate_disclosure.py \
  .agents/skills/patent-disclosure-distiller/examples/map-preload/output
```

输出包括：

- `disclosure.md`：带证据标签、章节、表格、待确认项和图文回指的底稿。
- `disclosure.docx`：`sample_exact` 样例 Word 模板的字节级副本；本示例只写附图方案，不嵌入实际图片。需要把新内容填入样例直接格式时，将 `docx_profile` 改为 `sample_fidelity`。
- `figure-plan.md`：三张附图的 imagegen 生成说明、底图路径、节点/边、图题和正文使用位置。
- `manifest.json`：输入摘要、证据统计、图号与文件、SHA-256 和自审状态。

若需要实际图稿，单独运行 imagegen 技能或用 PowerPoint 绘制底图，保存到 `source-figures/` 后将 `figure_output_mode` 改为 `rendered`；模板交付默认保持 `spec_only`。

Word 版式：`sample_exact` 原样复制样例 DOCX；`sample_fidelity` 使用样例的标题、正文、列表和直接格式 donor 填充新内容。两种模式都不引入自定义通用样式。
