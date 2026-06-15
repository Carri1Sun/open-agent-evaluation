# Case 与 Grader 添加/修改指导报告

本文档说明如何在本仓库中新增一个 evaluation case、给 case 添加 grader，以及如何修改已有 case。目标读者是 case 作者和评测规则维护者；通常不需要改 `src/` 下的 infra 代码。

## 1. 先理解边界

仓库分两层：

- 数据定义层：`cases/`、`schemas/`、`examples/`、`docs/`。新增或修改评测任务时，优先只改这里。
- 执行 infra 层：`src/open_agent_evaluation/`。只有新增 grader 类型、修改流水线、修改指标聚合时才需要改这里。

一次 agent submission 输入给评测系统时，核心有三项：

- `process`：完整过程，包括 thinking、tool call、observation、中间状态。
- `final_report`：最终汇报或最终答复。
- `artifacts`：最终产物文件，可以为空数组。

case 的职责是描述：

- 问题是什么，也就是 `question.query`。
- 期望输出什么，也就是 `output_contract`。
- 用哪些 grader 打分，也就是 `grader_files` 或内联 `graders`。

## 2. 新增一个 Case

### 2.1 选择集合

先判断 case 放到哪里：

- `cases/<family>/capability/`：能力探索集。用于看 agent 是否具备某类能力，汇总指标是 `pass@3`。
- `cases/<family>/regression/`：回归稳定集。用于防止已解决 case 退化，汇总指标是 `pass^3`。

slides 任务通常放在：

```text
cases/slides/capability/
cases/slides/regression/
```

### 2.2 新建目录

每个 case 必须是一个独立文件夹：

```text
cases/slides/capability/my_case_v1/
  case.json
  graders/
    deck_exists.json
    deck_structure.json
    quality.prompt.md
```

命名建议：

- 文件夹：`<short_task_name>_v1`，例如 `qbr_data_story_v1`。
- case id：`<family>.<task_type>.<short_name>_v1`，例如 `slides.data_story.qbr_v1`。
- grader id：稳定、短小、说明检查内容，例如 `deck_exists`、`deck_structure`、`quality_review`。

## 3. 写 case.json

最小结构：

```json
{
  "id": "slides.example.my_case_v1",
  "title": "My slide case",
  "task_family": "slides",
  "task_type": "data_presentation",
  "set": "capability",
  "question": {
    "query": "Create a 6 slide deck from the attached data.",
    "browser_initial_state": {
      "url": "about:blank",
      "auth_state": "not_required"
    },
    "attachments": []
  },
  "output_contract": {
    "required_artifacts": [
      { "id": "deck", "kind": "pptx", "extension": ".pptx", "required": true }
    ],
    "final_report": { "required": true }
  },
  "success_threshold": 0.8,
  "grader_files": [
    "graders/deck_exists.json",
    "graders/quality.prompt.md"
  ]
}
```

字段说明：

- `id`：全局唯一，后续 submission 用 `case_id` 对应它。
- `title`：给人看的标题。
- `task_family`：任务族，例如 `slides`。
- `task_type`：任务类型，例如 `data_presentation`、`research_brief`、`pitch_deck`。
- `set`：`capability` 或 `regression`，必须和目录语义一致。
- `question.query`：用户实际请求。
- `question.browser_initial_state`：浏览器初始状态。没有浏览器要求时可用 `about:blank`。
- `question.attachments`：输入附件列表。附件路径建议放在 case 文件夹的 `attachments/` 下。
- `output_contract.required_artifacts`：要求 agent 产出的文件。没有文件产物时写空数组。
- `success_threshold`：case 总分达到多少算通过。
- `grader_files`：本 case 使用的 grader 文件，相对 case 文件夹。

## 4. 添加 Grader

当前支持三种最常用的 case authoring 方式。

### 4.1 JSON Grader

适合确定性结构检查，例如文件是否存在、PPTX 是否有足够页数、是否有表格/图表。

示例：`graders/deck_exists.json`

```json
{
  "id": "deck_exists",
  "type": "artifact_presence",
  "weight": 0.2,
  "threshold": 1.0,
  "required": true,
  "config": {
    "artifacts": [
      { "id": "deck", "kind": "pptx", "extension": ".pptx", "required": true }
    ]
  }
}
```

示例：`graders/deck_structure.json`

```json
{
  "id": "deck_structure",
  "type": "pptx_structure",
  "weight": 0.4,
  "threshold": 0.8,
  "required": true,
  "config": {
    "artifact_id": "deck",
    "min_slides": 8,
    "max_slides": 12,
    "min_charts": 1,
    "min_tables": 1,
    "required_keywords": ["summary", "recommendation"],
    "require_widescreen": true
  }
}
```

常用 JSON grader 类型：

- `artifact_presence`：检查产物文件是否存在。
- `pptx_structure`：检查 PPTX slide 数、图表、表格、图片、speaker notes、关键词、宽屏比例。
- `trace_signal`：检查 `process` 中是否出现某些行为信号。

### 4.2 Prompt Grader

适合 LLM、PI agent、OpenCode agent 或人工评审。文件名建议用 `.prompt.md`。

示例：`graders/quality.prompt.md`

```markdown
---
id: quality_review
type: llm_judge
weight: 0.4
threshold: 0.75
required: false
---
Evaluate the submitted deck.

Score from 0 to 1 using these criteria:

- The deck answers the user query.
- The reasoning is evidence-backed.
- The visual style is coherent.

Return JSON with `score`, `passed`, `summary`, and `details`.
```

没有接外部 judge 时，这类 grader 会生成 prompt 并标记为 `skipped`。接外部 judge 时，可以改成 JSON grader 或在 config 中配置命令：

```json
{
  "id": "pi_review",
  "type": "agent_judge",
  "weight": 0.5,
  "threshold": 0.8,
  "required": false,
  "config": {
    "command": "pi-agent-review --output judge_result.json",
    "output_result_file": "judge_result.json",
    "timeout_seconds": 300
  }
}
```

外部 judge 必须返回或写出 JSON：

```json
{
  "score": 0.82,
  "passed": true,
  "summary": "The deck is evidence-backed and visually coherent.",
  "details": {
    "evidence": ["..."]
  }
}
```

### 4.3 Python Code Grader

适合检查 CSV、JSON、文件内容、最终汇报文本、产物文件列表等确定性条件。

示例：`graders/report_check.py`

```python
def grade(payload):
    final_report = payload["submission"]["final_report"]
    passed = "recommendation" in final_report.lower()
    return {
        "score": 1.0 if passed else 0.0,
        "passed": passed,
        "summary": "Final report mentions recommendation.",
        "details": {"checked": "final_report"}
    }
```

如果 Python grader 需要权重、阈值或 required 设置，在 `case.json` 中用对象引用：

```json
{
  "grader_files": [
    {
      "file": "graders/report_check.py",
      "weight": 0.3,
      "threshold": 1.0,
      "required": true
    }
  ]
}
```

## 5. 修改已有 Case

修改前先定位 case：

```bash
PYTHONPATH=src python3 -m open_agent_evaluation.cli list-cases --cases cases/slides
```

然后根据修改目标选择文件：

- 改用户问题：编辑该 case 的 `case.json` 中 `question.query`。
- 改浏览器起始状态：编辑 `question.browser_initial_state`。
- 改输入附件：编辑 `question.attachments`，并把附件放入该 case 文件夹。
- 改输出要求：编辑 `output_contract`。
- 改通过阈值：编辑 `success_threshold`。
- 改 grader 权重或阈值：编辑对应 grader 文件里的 `weight`、`threshold`、`required`。
- 改 LLM 评审标准：编辑 `.prompt.md` 正文。
- 改确定性代码逻辑：编辑 `.py` grader。
- 新增 grader：在 `graders/` 下新增文件，并把路径加入 `case.json` 的 `grader_files`。
- 删除 grader：从 `case.json` 的 `grader_files` 删除引用，再删除对应文件。

修改已有 case 的规则：

- 已经进入 `regression` 的 case 不建议随意改 query；如果需求变了，优先新建 `v2`。
- 如果只是修 typo 或让 grader 更严格，可以原地改。
- 如果改动会改变 case 语义，应该新建新 case id。
- `id` 一旦被 submission 或历史报告引用，尽量不要改。

## 6. 本地校验

每次新增或修改后，至少跑：

```bash
PYTHONPATH=src python3 -m open_agent_evaluation.cli validate-case --cases cases/slides
PYTHONPATH=src python3 -m open_agent_evaluation.cli list-cases --cases cases/slides
python3 -m unittest
```

如果只想检查 JSON 语法：

```bash
for f in $(rg --files -g '*.json'); do python3 -m json.tool "$f" >/dev/null || exit 1; done
```

## 7. 推荐工作流

新增 case：

1. 从已有 case 复制一个目录。
2. 改文件夹名、`id`、`title`、`question.query`。
3. 根据任务需要调整 `output_contract`。
4. 先保留 `artifact_presence` 这类硬检查。
5. 添加一个 `.prompt.md` 写开放性评审标准。
6. 如果有客观条件，再加 `.py` 或结构化 JSON grader。
7. 跑校验命令。

修改 case：

1. 先确认它是 `capability` 还是 `regression`。
2. 小修原地改，大改新建 `v2`。
3. 修改 query、prompt、grader 或阈值。
4. 跑校验命令。
5. 如果修改了 Python grader，补或更新单元测试。

## 8. 常见错误

- `case_id` 对不上：submission 的 `case_id` 必须等于 `case.json` 的 `id`。
- 忘记在 `grader_files` 引用新 grader：文件存在但不会执行。
- `required: true` 用得太多：会让 case 因某个非核心检查失败而直接失败。
- 只写 prompt 不接 judge：结果会是 `skipped`，适合设计阶段，不适合正式打分。
- regression case 改动过大：会污染历史对比，应该新建版本。
