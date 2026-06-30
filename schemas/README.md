# Schemas

本目录存放 Open Agent Evaluation 的 JSON Schema，用来约定 case、grader、submission 和 evaluation result 的文件结构。它们主要服务于三类场景：

- 帮助 case 作者按统一格式编写评测任务和评分规则。
- 帮助外部 agent runner 按统一格式提交候选结果。
- 帮助评测流水线输出稳定、可校验的结构化结果。

需要注意的是，schema 负责描述数据格式和可用字段；grader 的具体执行能力由 `src/open_agent_evaluation/` 中的实现决定。新增 grader type 或扩展 config 时，需要同步更新 schema、文档和运行时代码。

## 文件关系

一次完整评测可以理解为：

```text
evaluation_case + submission -> graders -> evaluation_result
```

- `evaluation_case.schema.json`：描述评测题目、期望输出和使用哪些 grader。
- `grader.schema.json`：描述单个 grader 的类型、权重、阈值和配置。
- `submission.schema.json`：描述 agent 对某个 case 的一次候选输出。
- `evaluation_result.schema.json`：描述评测流水线输出的结果和指标。

## evaluation_case.schema.json

`evaluation_case` 是评测任务定义，通常对应 `cases/` 下某个 case folder 里的 `case.json`。

主要字段：

- `id`：全局唯一的 case 标识，submission 通过 `case_id` 关联到它。
- `title`：给人阅读的 case 标题。
- `version`：case 版本号，用于表达任务定义或评分规则的演进。
- `task_family`：任务族，例如 `slides`。
- `task_type`：任务子类型，例如 `data_presentation`、`pitch_deck`、`research_brief`。
- `set`：case 所属集合，支持 `capability` 和 `regression`。
- `description`：case 的补充说明。
- `question`：用户任务输入的作者友好格式。
- `question.query`：用户原始请求。
- `question.browser_initial_state`：浏览器初始状态，例如起始 URL、登录要求或页面说明。
- `question.attachments`：任务附件列表。
- `question.attachments[].name`：附件名称。
- `question.attachments[].kind`：附件类型，例如 `csv`、`pdf`、`image`。
- `question.attachments[].path`：附件路径，必须是相对 case folder 的 `attachments/<file>` 路径。
- `question.attachments[].description`：附件用途说明。
- `input`：运行时归一化后的输入结构，兼容历史格式；作者优先编写 `question`。
- `input.user_query`：归一化后的用户请求。
- `input.browser_initial_state`：归一化后的浏览器初始状态。
- `input.browser_initial_state.resolved_local_files`：运行时解析出的本地附件绝对路径列表。
- `input.attachments`：归一化后的附件列表。
- `input.attachments[].resolved_path`：运行时解析出的附件绝对路径。
- `output_contract`：对候选输出的契约要求。
- `output_contract.required_artifacts`：必须或建议产出的文件列表。
- `output_contract.required_artifacts[].id`：产物标识，例如 `deck`。
- `output_contract.required_artifacts[].kind`：产物类型，例如 `pptx`。
- `output_contract.required_artifacts[].extension`：期望文件扩展名，例如 `.pptx`。
- `output_contract.required_artifacts[].required`：该产物是否为硬性要求。
- `output_contract.final_report`：最终回复的要求，可放置额外约束。
- `success_threshold`：case 总分达到该阈值后视为通过。
- `grader_files`：相对 case folder 的 grader 文件列表，适合 case 作者维护。
- `graders`：内联 grader specs 或 grader 文件引用。
- `graders[].id`：grader 标识。
- `graders[].type`：grader 类型。
- `graders[].weight`：grader 在 case 总分中的权重。
- `graders[].threshold`：该 grader 自身的通过阈值。
- `graders[].required`：该 grader 失败、跳过或报错时是否导致 case 失败。
- `graders[].config`：传给 grader 实现的配置对象。
- `graders[].file`：引用外部 grader 文件的路径。
- `metadata`：扩展元数据，例如作者、标签、维护说明。

## grader.schema.json

`grader` 是评分规则定义，可以写在 JSON 文件、case 的 `graders` 数组中，也可以由 `.prompt.md` 或 `.py` 文件加载生成。

主要字段：

- `id`：grader 的稳定标识。
- `type`：grader 类型。当前 schema 枚举了 `artifact_presence`、`pptx_structure`、`trace_signal`、`code`、`llm_judge`、`agent_judge`、`pi_agent_judge`、`external_command`、`scripted_command`、`rubric_prompt`。
- `weight`：该 grader 对 case 总分的权重。
- `threshold`：该 grader 的通过阈值，范围为 0 到 1。
- `required`：该 grader 是否为硬性要求。
- `prompt`：给 `llm_judge`、`agent_judge` 或 rubric 类 grader 使用的 prompt 文本。
- `prompt_path`：prompt 文件路径，通常相对 grader 文件。
- `code`：Python code grader 的代码字符串，必须定义 `grade(payload)`。
- `code_path`：Python code grader 的代码文件路径。
- `config`：grader 的扩展配置。不同 grader type 会读取不同配置，例如 artifact 列表、PPTX 结构要求、外部命令、超时时间等。

常见类型说明：

- `artifact_presence`：检查 submission 是否包含指定产物，以及文件是否存在。
- `pptx_structure`：解析 PPTX，检查页数、图表、表格、图片、关键词、宽屏比例等结构条件。
- `trace_signal`：在 `process` / trace 中搜索指定行为信号。
- `code`：运行 Python `grade(payload)` 函数并读取评分结果。
- `llm_judge`：准备或调用 LLM 评审。
- `agent_judge` / `pi_agent_judge`：准备或调用外部 agent 评审。
- `external_command`：调用外部命令，按统一 JSON 协议读取结果。
- `scripted_command`：语义上用于本地脚本检查，协议与 `external_command` 一致。
- `rubric_prompt`：生成 rubric prompt，供外部评审系统使用。

## submission.schema.json

`submission` 是评测流水线接收的候选产物输入格式，描述某个 agent 针对某个 case 的一次尝试。

主要字段：

- `case_id`：对应的 case id。
- `attempt_id`：本次尝试的标识，同一个 case 可以有多次尝试。
- `process`：agent 执行过程，可以是数组、对象或字符串，通常包含 thinking、tool call、observation 和中间状态。
- `final_report`：agent 面向用户的最终回复或总结。
- `trace_path`：外部 trace 文件路径；当 `process` 未内联提供时，运行时可以从该路径读取 trace。
- `artifacts`：agent 产出的最终文件列表，可以为空。
- `artifacts[].id`：产物标识，需要和 case 的 `output_contract` 或 grader config 对应。
- `artifacts[].kind`：产物类型，例如 `pptx`、`pdf`、`csv`。
- `artifacts[].path`：产物文件路径，相对 submission 文件所在目录或使用绝对路径。
- `artifacts[].description`：产物说明。
- `metadata`：运行元数据，例如模型、环境、耗时、runner 版本等。

## evaluation_result.schema.json

`evaluation_result` 是评测流水线的输出格式，包含 suite 级指标和每次尝试的 case 结果。

主要字段：

- `metrics`：整次评测的汇总指标。
- `metrics.attempt_count`：参与评测的 submission 尝试数。
- `metrics.case_count_with_results`：有评测结果的 case 数。
- `metrics.capability`：capability 集合的指标，例如 `pass_at_3`、通过 case、缺失 case。
- `metrics.regression`：regression 集合的指标，例如 `pass_power_3`、通过 case、尝试次数不足的 case。
- `results`：逐 case、逐 attempt 的评测结果列表。
- `results[].case_id`：被评测的 case id。
- `results[].attempt_id`：被评测的 attempt id。
- `results[].set`：case 所属集合。
- `results[].score`：case 聚合分数，范围为 0 到 1。
- `results[].passed`：case 是否通过。
- `results[].incomplete`：是否存在 skipped grader。
- `results[].required_failures`：失败、跳过或报错的 required grader id 列表。
- `results[].grader_results`：每个 grader 的评分结果。
- `results[].grader_results[].grader_id`：grader id。
- `results[].grader_results[].type`：grader type。
- `results[].grader_results[].score`：grader 分数，范围为 0 到 1。
- `results[].grader_results[].passed`：grader 是否通过。
- `results[].grader_results[].status`：grader 状态，支持 `passed`、`failed`、`skipped`、`error`。
- `results[].grader_results[].summary`：grader 对结果的一句话说明。
- `results[].grader_results[].details`：结构化证据、错误信息或调试数据。
