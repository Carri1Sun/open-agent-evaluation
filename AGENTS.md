# AGENTS.md

## 回复与协作规则

- 对用户回复使用中文。
- 文档、说明和对话保持直接、清晰、可执行。
- 避免使用先否定一个表述、再转向另一个表述的对照句式。
- 提交信息使用 Conventional Commit 类型，主题行需要概括全部变更。

提交信息格式：

```text
<type>: <summary of all changes>
- <change summary 1>
- <change summary 2>
```

允许的 type：`feat`、`fix`、`refactor`、`chore`、`docs`、`test`、`perf`。

## 仓库概述

`open-agent-evaluation` 是面向 general agent 任务候选输出的评测系统骨架。仓库负责定义任务输入、候选输出、evaluation case、grader、评测流水线和结果指标；agent 的实际执行由外部系统完成。

当前重点是 slides/PPT 生成任务评测，覆盖 capability set 和 regression set：

- capability set 用 `pass@3` 衡量能力入口，前三次尝试中任意一次通过即计入通过。
- regression set 用 `pass^3` 衡量稳定性，前三次尝试全部通过才计入通过。
- case folder 以 `case.json` 和 `graders/` 组织任务与评分规则。
- deterministic grader 覆盖产物存在、PPTX 结构、trace 信号等客观检查。
- code、external、LLM/agent judge 入口用于扩展更复杂的本地脚本和开放性评审。

## 目录职责

- `src/open_agent_evaluation/`：评测运行时实现。
- `src/open_agent_evaluation/models.py`：case、submission、grader result、case result、suite result 数据结构。
- `src/open_agent_evaluation/case_loader.py`：发现 case folder，加载 `case.json`、grader 文件和 submission。
- `src/open_agent_evaluation/pipeline.py`：执行 grader、聚合 case 分数、生成 suite result。
- `src/open_agent_evaluation/metrics.py`：计算 `pass@k` 和 `pass^k`。
- `src/open_agent_evaluation/cli.py`：命令行入口 `open-agent-eval`。
- `src/open_agent_evaluation/graders/`：grader registry 和具体 grader 实现。
- `cases/slides/`：slides capability/regression case folders。
- `schemas/`：case、grader、submission、evaluation result 的 JSON Schema。
- `examples/`：submission 和 result 示例。
- `tests/`：不依赖外部服务的单元测试。
- `docs/manuel/`：说明类型文档，指导人或 agent 为仓库添加内容。
- `docs/technical/`：技术架构与实现设计文档。
- `docs/product/`：产品设计、评测设计和任务设计文档。

## 关键文档

- `docs/manuel/authoring_cases.md`：新增或修改 case 与 grader 的指导报告。
- `docs/technical/repository_design.md`：仓库模块、数据流和扩展方式。
- `docs/product/slides_evaluation_design.md`：slides 任务类型、评测标准和 grader 设计。
- `schemas/README.md`：JSON Schema 字段说明和数据协议。

## 数据流

```text
case folders + submissions
  -> case_loader
  -> EvaluationRunner
  -> GraderRegistry
  -> grader results
  -> case result
  -> suite metrics
  -> JSON report
```

每个 submission 至少包含：

- `case_id`：关联 `case.json` 里的 `id`。
- `attempt_id`：一次尝试的稳定标识。
- `process` 或 `trace_path`：agent 执行过程。
- `final_report`：面向用户的最终回复。
- `artifacts`：候选产物列表，可为空数组。

## Grader 类型

默认 registry 支持这些类型：

- `artifact_presence`：检查 required artifacts 是否声明且文件存在。
- `pptx_structure`：解析 PPTX 的 Office Open XML，检查页数、图表、表格、图片、关键词、宽屏比例、speaker notes、文本密度等。
- `trace_signal`：在 submission trace 中搜索行为信号。
- `rubric_prompt`：生成 rubric prompt，适合设计阶段或外部评审系统接入。
- `code`：运行 Python `grade(payload)` 并读取 JSON 结果。
- `external_command` / `scripted_command`：调用外部命令，从 stdout 或 `output_result_file` 读取 JSON 结果。
- `llm_judge`：准备或转发 LLM judge 评审。
- `agent_judge` / `pi_agent_judge`：准备或转发外部 agent judge 评审。

新增 grader type 时，同步更新：

- `src/open_agent_evaluation/graders/` 中的实现。
- `src/open_agent_evaluation/graders/registry.py` 的注册逻辑。
- `schemas/grader.schema.json` 的类型和 config 说明。
- `docs/manuel/authoring_cases.md` 或相关设计文档。
- 覆盖关键行为的单元测试。

## Case 编写约定

推荐每个 case 一个目录：

```text
cases/<task_family>/<set>/<case_slug>/
  case.json
  graders/
    deck_exists.json
    deck_structure.json
    quality.prompt.md
  attachments/
    optional_input.csv
```

约定：

- `set` 只能是 `capability` 或 `regression`，并与目录语义保持一致。
- `id` 需要全局唯一，submission 通过 `case_id` 精确关联。
- 作者优先写 `question.query`，运行时会归一化到 `input.user_query`。
- `grader_files` 使用相对 case folder 的路径。
- `.json` grader 适合结构化确定性检查。
- `.prompt.md` grader 适合 LLM、agent 或人工评审标准。
- `.py` grader 必须定义 `grade(payload)` 并返回包含 `score`、`passed`、`summary`、`details` 的 dict。
- 已进入 regression 的 case 需要保持 query 和语义稳定；任务语义变化时新增版本。

## 本地命令

安装开发包：

```bash
python3 -m pip install -e .
```

运行测试：

```bash
python3 -m unittest
```

校验并列出 case：

```bash
PYTHONPATH=src python3 -m open_agent_evaluation.cli validate-case --cases cases/slides
PYTHONPATH=src python3 -m open_agent_evaluation.cli list-cases --cases cases/slides
```

运行评测：

```bash
open-agent-eval run \
  --cases cases/slides \
  --submissions path/to/submission_dir \
  --output reports/run.json \
  --pretty
```

检查 JSON 语法：

```bash
for f in $(rg --files -g '*.json'); do python3 -m json.tool "$f" >/dev/null || exit 1; done
```

## 实现注意事项

- 读取文件和搜索内容优先使用 `rg` / `rg --files`。
- 保持 case 数据、schema、运行时代码和文档一致。
- 修改 shared runtime、grader 聚合逻辑或 schema 时补充测试。
- 避免把外部服务依赖引入默认单元测试；默认测试应能离线运行。
- 外部 judge 通过统一 JSON 协议接入：stdin 接收 payload，stdout 或 `output_result_file` 输出评分 JSON。
- 保留用户已有改动，不要回滚与当前任务无关的文件。
