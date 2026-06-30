# open-agent-evaluation

面向 general agent 任务的评测系统骨架。本仓库的边界是定义任务输入、候选输出、评测 case、grader 和流水线；agent 执行由外部系统完成。

当前重点实现 slides/PPT 生成任务评测，支持：

- capability set：衡量模型/agent 能覆盖哪些 slides 能力，默认按 `pass@3` 汇总。
- regression set：沉淀已经解决的稳定性样例，默认按 `pass^3` 汇总。
- case folder：每个 case 一个文件夹，包含 `case.json` 和 `graders/`。
- deterministic grader：检查产物存在、PPTX 结构、图表/表格/图片、关键词、版式密度等。
- code/LLM/agent grader：支持 Python 代码 grader、Markdown prompt grader、外部 LLM/PI/OpenCode agent 评审。

## 快速开始

```bash
python3 -m pip install -e .
python3 -m unittest
open-agent-eval list-cases --cases cases/slides
```

运行评测时传入一个或多个 submission 目录或文件：

```bash
open-agent-eval run \
  --cases cases/slides \
  --submissions path/to/submission_dir \
  --output reports/run.json
```

临时运行可以使用 `PYTHONPATH=src python3 -m open_agent_evaluation.cli ...`。

submission 目录需要包含 `submission.json`。核心输入是 `process`、`final_report`、`artifacts` 三项，其中 `artifacts` 可以为空，示例结构见 `schemas/submission.schema.json`。

## 目录

- `docs/product/slides_evaluation_design.md`：slides 任务类型、评测标准和 grader 设计。
- `docs/technical/repository_design.md`：仓库模块、数据流和扩展方式。
- `docs/manuel/authoring_cases.md`：新增/修改 case 和 grader 的指导报告。
- `schemas/`：evaluation case 与 submission 的 JSON Schema。
- `cases/slides/`：slides capability/regression case folders。
- `src/open_agent_evaluation/`：评测流水线实现。
- `examples/`：输入与输出示例。
- `tests/`：不依赖外部服务的单元测试。
