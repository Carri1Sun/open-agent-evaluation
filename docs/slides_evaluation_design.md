# Slides 生成任务评测设计

本文档定义 general agent 在 slides/PPT 生成任务上的评测方法。目标不是替代人工审美，而是把可客观验证的部分自动化，把主观判断拆成稳定、可复用、可解释的 grader。

## 1. 任务边界

仓库只评测 agent 产出的结果，不负责运行 agent。一次 slides 评测接收：

- 用户 query。
- 浏览器初始状态，例如起始 URL、登录状态、页面说明。
- 附件，例如 CSV、PDF、DOCX、图片素材、品牌规范。
- 候选输出，例如 `.pptx`、导出的图片/PDF、最终回复、执行 trace。

输出是结构化评测结果：每个 grader 的分数、通过状态、证据、失败原因，以及 case 层和 suite 层汇总指标。

## 2. Slides 任务类型

### 2.1 数据呈现型

代表任务：QBR、经营周报、销售漏斗、实验结果汇报、财务摘要。

核心标准：

- 内容忠实：关键数值、时间范围、口径、单位与输入数据一致。
- 数据转译：能把原始数据转成结论、趋势、异常点和建议。
- 可视化匹配：趋势用折线，构成用柱状/堆叠/饼图，关系用散点，流程用步骤图。
- 产物完整：应包含图表、必要表格、结论页和行动建议页。
- 可读性：图表标题、轴、单位、注释清楚，避免过密。

推荐 grader：

- deterministic：检查 PPTX slide 数、chart/table/image 数、关键词、附件引用、输出文件。
- scripted data check：通过 `scripted_command` 解析图表数据或伴随 CSV，核对关键指标。
- visual/rubric：评估图表选择是否符合意图，是否有数据故事线。

### 2.2 调研汇报型

代表任务：行业研究、竞品分析、用户研究、政策解读、市场进入建议。

核心标准：

- 证据质量：来源可靠、信息新、引用清楚。
- 交叉验证：关键结论至少由多个独立证据支持。
- 观点结构：有问题定义、发现、证据、推理、建议。
- 风险意识：指出不确定性、反例和边界条件。
- 表达适配：适合汇报对象，不堆砌材料。

推荐 grader：

- trace grader：检查搜索、阅读、交叉验证、引用整理等行为信号。
- external agent grader：让 PI/OpenCode/LLM 读取 trace 与产物，按证据覆盖率评分。
- visual/rubric：评估结构、结论力度和信息层级。

### 2.3 Pitch/叙事型

代表任务：融资路演、产品发布、项目提案、销售 deck。

核心标准：

- 叙事弧线：痛点、解决方案、证明、计划、请求清晰。
- 受众匹配：投资人、客户、管理层看到的信息重点不同。
- 说服力：每页服务于一个明确论点。
- 视觉节奏：标题页、章节页、内容页、总结页有节奏变化。
- 品牌一致：颜色、字体、语气与品牌或场景一致。

推荐 grader：

- deterministic：检查章节关键词、slide 范围、图片/图示存在。
- `llm_judge`：评估叙事完整度、受众适配、视觉一致性。

### 2.4 教学/培训型

代表任务：课程讲义、员工培训、操作手册、工作坊材料。

核心标准：

- 学习路径：目标、概念、示例、练习、复盘完整。
- 难度递进：从基础到复杂，避免跳步。
- 可执行性：步骤、截图、检查清单明确。
- 互动设计：练习、问题、讨论或测验。
- 可复用：讲者备注或补充材料足够。

推荐 grader：

- deterministic：检查练习页、总结页、speaker notes、截图/图片。
- rubric：评估教学节奏和可操作性。

### 2.5 视觉改写/品牌套用型

代表任务：把已有材料改成公司模板、统一视觉、精简重排。

核心标准：

- 信息保真：原始内容没有丢失关键点。
- 视觉一致：颜色、字体、组件、间距、图标体系一致。
- 信息层级：标题、正文、图表、注释清晰分层。
- 版式质量：对齐、留白、密度、比例稳定。

推荐 grader：

- deterministic：检查 slide 数范围、图片数、关键词保留。
- visual comparator：渲染前后图片，检查溢出、空白页、视觉一致性。
- rubric：评估设计感。

## 3. 评分维度

建议把 slides case 分成四个维度，每个 case 按需求配置权重。

- Contract：是否生成了要求格式和数量的产物。
- Content：事实、数据、结构、结论是否满足任务。
- Workflow：trace 中是否体现了必要的收集、验证、制作流程。
- Presentation：图表、版式、风格、可读性、受众适配。

Deterministic grader 优先覆盖 Contract 与部分 Content/Presentation。LLM 或 agent grader 覆盖开放性的 Content、Workflow 和 Presentation。

## 4. Capability 与 Regression

capability set 用来理解能力边界，允许探索性和开放性 case。每个 case 建议至少跑 3 次，用 `pass@3` 衡量：3 次里有一次达到成功阈值即说明当前系统具备该能力入口。

regression set 来自已经解决并稳定的 capability case。每个 case 建议跑 3 次，用 `pass^3` 衡量：前 3 次全部通过才算稳定。它不追求覆盖广，而追求发现退化。

## 5. Slides Grader 设计

### 5.1 Artifact Presence

检查候选输出是否包含必需产物，例如 `deck.pptx`、导出 PDF、附带数据文件。失败通常是硬失败。

### 5.2 PPTX Structure

直接解析 PPTX 的 Office Open XML：

- slide 数是否在范围内。
- 是否包含图表、表格、图片。
- 是否包含任务关键词或章节关键词。
- 是否使用 16:9 宽屏。
- 非空页面比例。
- 单页文本密度是否过高。
- speaker notes 页数是否满足培训类任务。

这类 grader 不判断审美好坏，但能抓住很多明显失败。

### 5.3 Scripted Data Check

针对数据型 slides，case 可以提供专门脚本：

- 读取输入 CSV/JSON 和候选产物附带的数据。
- 校验关键数值、排序、过滤条件、单位换算。
- 校验图表对应的数据列和聚合口径。

实现上使用 `scripted_command` grader，它与 `external_command` 协议相同，但语义上用于确定性的本地脚本。

### 5.4 Trace Signal

把 trace 当作行为证据，检查：

- 是否打开/读取了给定附件。
- 是否进行了搜索、浏览、抽取、交叉验证。
- 是否生成并检查了中间产物。
- 是否渲染或预览了 slides。

它只能证明行为信号存在，不能单独证明产物正确。

### 5.5 Rubric Prompt

把开放问题拆成可评分标准，并放在 `.prompt.md` grader 文件中，例如：

- 图表是否与用户意图匹配。
- 结论是否由证据支持。
- 视觉风格是否一致。
- 受众是否能快速理解。

本仓库不绑定具体 LLM，`llm_judge` 默认生成评审 payload；实际执行可通过 `command` 接入 LLM、PI agent、OpenCode agent 或人工系统。

### 5.6 External Command

复杂 grader 统一走外部命令协议：

- 输入：case、submission、grader config 的 JSON。
- 输出：`score`、`passed`、`summary`、`details` 的 JSON。

这样可以在不修改核心流水线的情况下接入更强的评审 agent。

## 6. 两轮自检结果

第一轮设计自检：

- 确定性标准和主观标准已分离，避免用单轮 LLM 判断所有问题。
- capability/regression 的统计目标不同，分别对应探索能力和稳定性。
- slides 任务类型覆盖数据、调研、pitch、培训、视觉改写五类常见需求。

第二轮设计自检：

- PPTX 静态检查只能发现结构性问题，不能替代视觉和事实判断，因此保留 external/rubric 扩展。
- 数据型 slides 需要 case-specific scripted grader，不能只看是否存在 chart。
- trace 信号只作为流程证据，最终仍要结合产物评分。
