# Dify DSL YAML 格式完整参考

本文档定义了 Dify DSL（Domain Specific Language）YAML 的完整格式规范，用于生成可导入 Dify 的工作流配置。

> ⚠️ **重要**：默认使用 DSL `0.6.0` 版本格式。0.7.0+ 的功能（如 structured_output、error_handle_mode 等）在 0.6.0 环境中会导致导入失败。详见 `dsl-pitfalls.md`。

## 1. 顶层结构

```yaml
kind: app                    # 必填，固定为 "app"
version: 0.6.0               # 必填，DSL 版本号（不加引号）

app:                         # 应用元数据
  name: "应用名称"
  description: "应用描述"
  mode: workflow             # workflow | advanced-chat | agent | chat
  icon: "🤖"
  icon_background: "#FFEAD5"
  icon_type: emoji           # emoji | image | link
  use_icon_as_answer_icon: false

workflow:                    # 工作流定义
  environment_variables: []  # 环境变量
  conversation_variables: [] # 会话变量（Chatflow 专用）
  features: {}               # 功能配置（见第7节，必须完整）
  graph:                     # 工作流图
    nodes: []                # 节点列表
    edges: []                # 边列表
    viewport:                # 画布视口
      x: 0
      y: 0
      zoom: 0.4
  rag_pipeline_variables: [] # 必需，即使为空

dependencies:                # 插件依赖（不能为空数组！需列出用到的插件）
  - current_identifier: null
    type: package
    value:
      plugin_unique_identifier: langgenius/deepseek-4399:0.0.15@xxx
      version: null
```

### mode 字段说明

| mode 值 | 应用类型 | 终点节点 | 说明 |
|---------|---------|---------|------|
| `workflow` | Workflow | `end` | 一次执行到底的 DAG 流程 |
| `advanced-chat` | Chatflow | `answer` | 带对话层的工作流 |
| `agent` | Agent | - | 智能体应用 |
| `chat` | Chatbot | - | 简单聊天助手 |

> ⚠️ Workflow 模式的终点节点类型是 `end`（不是 `output`），输出字段是 `outputs`（不是 `variables`）。

## 2. 节点（Node）通用结构

所有节点共享以下基础结构：

```yaml
- id: '1745000000001'       # 必填，纯数字字符串（不要用语义化命名）
  type: "custom"             # 必填，固定为 "custom"（React Flow 类型）
  width: 242                 # 必填，UI 宽度
  height: 116                # 必填，UI 高度
  selected: false            # 必填
  sourcePosition: right      # 必填
  targetPosition: left       # 必填
  position:                  # 必填，画布坐标
    x: 80
    y: 282
  positionAbsolute:          # 必填，绝对坐标（非迭代子节点 = position）
    x: 80
    y: 282
  data:                      # 必填，节点配置
    type: "start"            # 必填，节点类型（见节点类型表）
    title: "节点标题"         # 必填，显示名称
    selected: false          # 必填
    # 以下字段根据 type 不同而变化
```

### 节点 ID 命名规范

> ⚠️ **节点 ID 必须是纯数字字符串**，不能使用语义化命名。Dify 导出时使用时间戳格式的数字。

| 规则 | 示例 | 说明 |
|------|------|------|
| 纯数字字符串 | `'1745000000001'` | ✅ 正确 |
| 语义化命名 | `start`, `llm_1` | ❌ 错误，导入会失败 |

## 3. 边（Edge）结构

边定义节点间的连接关系：

```yaml
- data:                        # 必填
    isInIteration: false       # 必填，迭代内部边为 true
    isInLoop: false            # 必填
    sourceType: start          # 必填，源节点类型
    targetType: code           # 必填，目标节点类型
  id: 'xxx-source-yyy-target' # 必填，格式为 {source}-source-{target}-{targetHandle}
  source: '1745000000001'      # 必填，源节点 ID
  sourceHandle: "source"       # 必填，源句柄
  target: '1745000000002'      # 必填，目标节点 ID
  targetHandle: "target"       # 必填，目标句柄
  type: "custom"               # 必填
  zIndex: 0                    # 必填，迭代内部边为 1002
```

### sourceHandle 值说明

| 节点类型 | sourceHandle 值 | 说明 |
|---------|-----------------|------|
| 普通节点 | `source` | 默认输出 |
| IF/ELSE | `case_id`（如 `case_1`） | IF 分支 |
| IF/ELSE | `else` | ELSE 分支 |
| Iteration | `iteration_start` | 迭代开始 |
| Iteration | `source` | 迭代结束（输出） |

### 画布布局规则

- 主流程节点从左到右排列，x 坐标递增（步长约 304）
- 分支节点垂直分布，y 坐标上下偏移（步长约 200）
- 起始位置建议 `x: 30, y: 200`

## 4. 变量引用语法

```yaml
{{#start.query#}}              # 引用 start 节点的 query 变量
{{#llm_1.text#}}               # 引用 LLM 节点的输出文本
{{#code_1.result#}}            # 引用代码节点的 result 输出
{{#knowledge_1.result#}}       # 引用知识库检索结果
{{#conversation.user_name#}}   # 引用会话变量
{{#env.API_KEY#}}              # 引用环境变量
{{variable_name}}              # 在 LLM prompt 文本中的简化引用
```

## 5. 环境变量

工作区级别变量，所有工作流共享：

```yaml
environment_variables:
  - name: "API_KEY"
    value: "sk-xxxxxxxx"
    value_type: "string"       # string | number | secret
  - name: "MAX_RETRIES"
    value: 3
    value_type: "number"
```

## 6. 会话变量

Chatflow 专用，跨对话轮次持久化：

```yaml
conversation_variables:
  - name: "user_preferences"
    value_type: "object"       # string | number | object | array[string]
    value:
      language: "zh"
      tone: "professional"
  - name: "conversation_history"
    value_type: "array[string]"
    value: []
```

## 7. features 配置

features 必须包含完整的 file_upload 配置：

```yaml
features:
  file_upload:
    allowed_file_extensions:
      - .JPG
      - .JPEG
      - .PNG
      - .GIF
      - .WEBP
      - .SVG
    allowed_file_types:
      - image
    allowed_file_upload_methods:
      - local_file
      - remote_url
    enabled: false
    fileUploadConfig:                    # 必需！
      attachment_image_file_size_limit: 2
      audio_file_size_limit: 50
      batch_count_limit: 5
      file_size_limit: 100
      file_upload_limit: 20
      image_file_batch_limit: 10
      image_file_size_limit: 10
      single_chunk_attachment_limit: 10
      video_file_size_limit: 100
      workflow_file_upload_limit: 10
    image:                               # 必需！
      enabled: false
      number_limits: 3
      transfer_methods:
        - local_file
        - remote_url
    number_limits: 3
  opening_statement: ''
  retriever_resource:
    enabled: true
  sensitive_word_avoidance:
    enabled: false
  speech_to_text:
    enabled: false
  suggested_questions: []
  suggested_questions_after_answer:
    enabled: false
  text_to_speech:
    enabled: false
    language: ''
    voice: ''
```

## 8. DSL 版本兼容性

| 版本范围 | 兼容状态 | 说明 |
|---------|---------|------|
| 相同版本 | COMPLETED | 完全兼容 |
| 次版本较低 | COMPLETED_WITH_WARNINGS | 带警告导入 |
| 主版本较低 | PENDING | 需用户确认 |
| 版本更高 | PENDING | 需用户确认 |

**生成 YAML 时默认使用 `0.6.0` 版本**（不加引号）。如果用户确认其 Dify 版本 ≥ 0.7.0，才使用 `0.7.0`。

## 9. YAML 生成检查清单

生成 YAML 前逐项检查：

- [ ] `kind: app` 和 `version: 0.6.0`（不加引号）存在
- [ ] `app.mode` 与应用类型匹配（workflow / advanced-chat）
- [ ] `app.use_icon_as_answer_icon: false` 存在
- [ ] `dependencies` 不为空数组（列出用到的插件）
- [ ] 所有节点 ID 是纯数字字符串（如 `'1745000000001'`）
- [ ] 所有节点有 `type: custom`、`selected`、`sourcePosition`、`targetPosition`
- [ ] 所有节点有 `position` 和 `positionAbsolute`
- [ ] 所有节点有 `width` 和 `height`
- [ ] 所有节点 `data.selected: false` 存在
- [ ] 每个节点（除终点）都有至少一条出边
- [ ] 每个节点（除 start）都有至少一条入边
- [ ] 所有边有 `data`（含 `isInIteration`、`isInLoop`、`sourceType`、`targetType`）
- [ ] 所有边有 `id`、`type: custom`、`zIndex`
- [ ] 变量引用 `{{#node_id.var#}}` 中的 node_id 存在
- [ ] 知识库 `dataset_ids` 使用真实 ID（导入后用户替换）
- [ ] 模型 `provider` 使用完整路径格式（如 `langgenius/deepseek-4399/deepseek`）
- [ ] LLM 节点 `structured_output_enabled: false`，不写 `structured_output` 块
- [ ] LLM 节点不写 `memory`（Workflow 模式）
- [ ] LLM `prompt_template` 每个 item 有 `id`（UUID）
- [ ] Workflow 类型以 `type: end` 节点结束（不是 `type: output`）
- [ ] End 节点用 `outputs`（不是 `variables`），每个输出有 `value_type`
- [ ] Start 变量不写 `max_length`
- [ ] Code 节点变量有 `value_type` 字段
- [ ] 知识检索有 `query_attachment_selector: []`
- [ ] 知识检索不写 `score_threshold` 和 `score_threshold_enabled`
- [ ] 迭代节点不写 `error_handle_mode`、`is_parallel`、`parallel_nums`、`output_type`
- [ ] 迭代节点有 `start_node_id` 指向 iteration-start 节点
- [ ] iteration-start 节点 `type: custom-iteration-start`
- [ ] 迭代子节点有 `parentId`、`zIndex: 1002`、`isInIteration`、`iteration_id`
- [ ] 迭代子节点 `positionAbsolute` = 父节点 position + 子节点 position
- [ ] `workflow.rag_pipeline_variables: []` 存在
- [ ] `features.file_upload` 包含完整的 `fileUploadConfig` 和 `image` 子配置
- [ ] 所有 Code 节点的代码带中文注释（每步说明在做什么、兜底逻辑说明、return 输出说明）
