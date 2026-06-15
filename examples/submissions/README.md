# Submission 示例

`submission.json` 是一次 agent 尝试的输出索引。真实评测时，把 agent 过程、最终汇报、生成文件放在同一目录，并在 `artifacts` 中引用生成文件。没有文件产物时，`artifacts` 可以是空数组。

最小结构：

```json
{
  "case_id": "slides.regression.chart_table_v1",
  "attempt_id": "run_1",
  "process": [
    { "type": "tool", "name": "python", "text": "read sales.csv and created chart" },
    { "type": "tool", "name": "preview", "text": "rendered deck screenshot" }
  ],
  "final_report": "I created the requested deck at deck.pptx.",
  "artifacts": [
    { "id": "deck", "kind": "pptx", "path": "deck.pptx" }
  ],
  "metadata": {
    "model": "example-agent",
    "created_at": "2026-06-15T00:00:00Z"
  }
}
```
