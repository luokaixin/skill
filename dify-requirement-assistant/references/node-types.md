# Dify 工作流节点类型配置参考

本文档列出 Dify 工作流支持的所有节点类型及其 YAML 配置模板。

## 节点类型速查表

| 节点类型 | data.type 值 | 用途 | 适用场景 |
|---------|-------------|------|---------|
| 开始 | `start` | 定义输入变量，工作流入口 | 所有工作流 |
| LLM | `llm` | 调用语言模型 | 文本生成、分析、推理 |
| 知识库检索 | `knowledge-retrieval` | 从知识库检索 | RAG 问答 |
| 代码执行 | `code` | 执行 Python/JS | 数据处理、转换 |
| 条件分支 | `if-else` | 条件判断路由 | 流程控制 |
| HTTP 请求 | `http-request` | 调用外部 API | 外部集成 |
| 模板转换 | `template-transform` | Jinja2 模板渲染 | 文本格式化 |
| 问题分类器 | `question-classifier` | LLM 分类问题 | 意图识别 |
| 参数提取器 | `parameter-extractor` | LLM 提取结构化参数 | 参数解析 |
| 回答 | `answer` | 返回响应（Chatflow） | Chatflow 终点 |
| 变量赋值 | `variable-assigner` | 写入变量 | 状态管理 |
| 变量聚合器 | `variable-aggregator` | 合并多分支变量 | 分支汇聚 |
| 迭代 | `iteration` | 遍历列表执行子流程 | 批量处理 |
| 循环 | `loop` | 条件循环 | 重复任务 |
| 列表操作 | `list-operator` | 过滤/排序列表 | 数据处理 |
| 文档提取器 | `doc-extractor` | 提取文档文本 | 文件处理 |
| 输出 | `end` | 工作流输出 | Workflow 终点 |
| Agent | `agent` | 智能体节点 | 自主决策 |
| 工具 | `tool` | 调用工具 | 工具集成 |

---

## 1. Start 节点（开始）

```yaml
- id: '1745000000001'
  type: "custom"
  position: {x: 80, y: 282}
  positionAbsolute: {x: 80, y: 282}
  selected: false
  sourcePosition: right
  targetPosition: left
  width: 242
  height: 116
  data:
    type: "start"
    title: "开始"
    selected: false
    variables:
      - variable: "query"
        label: "用户问题"
        type: "paragraph"
        required: true
        default: ''
        hint: ''
        options: []
        placeholder: ''
      - variable: "platform"
        label: "平台"
        type: "select"
        options:
          - "微信"
          - "抖音"
          - "小红书"
        required: true
        default: ''
        hint: ''
        placeholder: ''
```

> ⚠️ **0.6.0 注意**：变量不要写 `max_length` 字段。每个变量必须有 `default`、`hint`、`options`、`placeholder` 字段。

### 变量类型说明

| type 值 | 说明 | 额外字段 |
|---------|------|---------|
| `text-input` | 短文本 | 无 max_length |
| `paragraph` | 长文本 | 无 max_length |
| `select` | 下拉选择 | `options: [...]` |
| `number` | 数字 | `default` |

---

## 2. LLM 节点

```yaml
- id: '1745000000003'
  type: "custom"
  position: {x: 684, y: 282}
  positionAbsolute: {x: 684, y: 282}
  selected: false
  sourcePosition: right
  targetPosition: left
  width: 242
  height: 98
  data:
    type: "llm"
    title: "LLM 节点"
    selected: false
    model:
      provider: "langgenius/deepseek-4399/deepseek"  # 完整路径格式
      name: "deepseek-v4-pro"
      mode: "chat"
      completion_params:
        temperature: 0.7
    prompt_template:
      - id: "<uuid>"              # 必需，使用 UUID
        role: "system"
        text: "你是一个专业的助手。"
      - id: "<uuid>"              # 必需，使用 UUID
        role: "user"
        text: "{{#1745000000001.query#}}"
    context:
      enabled: false
      variable_selector: []
    vision:
      enabled: false
    structured_output_enabled: false  # 0.6.0 必须为 false
```

### ⚠️ 0.6.0 LLM 节点注意事项

1. **不要写 `structured_output` 块** — 0.7.0+ 才支持，会导致导入失败
2. **`structured_output_enabled` 必须为 `false`** — 如需结构化输出，在 prompt 中要求 JSON，用 Code 节点解析
3. **Workflow 模式不要写 `memory`** — 只有 Chatflow 才需要
4. **`provider` 使用完整路径** — 如 `langgenius/deepseek-4399/deepseek`，不是简单的 `openai`
5. **`prompt_template` 每个 item 必须有 `id`** — 使用 UUID

### LLM 节点输出变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `text` | string | 模型生成的文本 |
| `usage` | object | token 使用统计 |

---

## 3. Knowledge Retrieval 节点（知识库检索）

```yaml
- id: '1745000000002'
  type: "custom"
  position: {x: 382, y: 282}
  positionAbsolute: {x: 382, y: 282}
  selected: false
  sourcePosition: right
  targetPosition: left
  width: 242
  height: 90
  data:
    type: "knowledge-retrieval"
    title: "知识检索"
    selected: false
    query_variable_selector:
      - '1745000000001'
      - query
    query_attachment_selector: []          # 必需，即使为空
    dataset_ids:
      - "lKvsl7j77SH5nq69ND+xe+gSnQgKOJH2hIwuFJNmYCMxlLVrDWCLdD5vXG4BeQip"  # 真实 ID
    retrieval_mode: "multiple"
    multiple_retrieval_config:
      top_k: 4
      reranking_enable: true
      reranking_mode: "reranking_model"
      reranking_model:
        provider: "langgenius/tongyi-4399/tongyi"
        model: "qwen3-vl-rerank"
```

> ⚠️ **0.6.0 注意**：
> - 必须有 `query_attachment_selector: []`
> - **不要写 `score_threshold` 和 `score_threshold_enabled`**
> - `dataset_ids` 用真实 ID（导入后用户替换），不要用 `YOUR_DATASET_ID` 占位符

### 输出变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `result` | array[object] | 检索到的知识片段列表 |

---

## 4. Code 节点（代码执行）

```yaml
- id: '1745000000004'
  type: "custom"
  position: {x: 638, y: 200}
  positionAbsolute: {x: 638, y: 200}
  selected: false
  sourcePosition: right
  targetPosition: left
  width: 242
  height: 54
  data:
    type: "code"
    title: "代码节点"
    selected: false
    variables:
      - variable: "input_text"
        value_selector:
          - '1745000000001'
          - query
        value_type: string          # 必需！
      - variable: "count"
        value_selector:
          - '1745000000001'
          - count
        value_type: number          # 必需！
    code_language: "python3"
    code: |
      def main(input_text: str, count: int) -> dict:
          result = input_text.upper()
          return {"result": result, "count": count}
    outputs:
      result:
        type: "string"
        children: null
      count:
        type: "number"
        children: null
```

> ⚠️ **0.6.0 注意**：Code 节点的每个变量必须有 `value_type` 字段。

### Code 节点输出类型

| type 值 | 说明 | children |
|---------|------|----------|
| `string` | 字符串 | null |
| `number` | 数字 | null |
| `boolean` | 布尔 | null |
| `object` | 对象 | 子字段定义 |
| `array[string]` | 字符串数组 | null |
| `array[object]` | 对象数组 | 子字段定义 |

---

## 5. IF/ELSE 节点（条件分支）

```yaml
- id: "if_else_1"
  type: "custom"
  position: {x: 638, y: 200}
  data:
    type: "if-else"
    title: "条件判断"
    cases:
      - case_id: "case_1"
        logical_operator: "and"     # and | or
        conditions:
          - variable_selector:
              - "llm_1"
              - "text"
            comparison_operator: "contains"
            value: "关键词"
      - case_id: "case_2"
        logical_operator: "or"
        conditions:
          - variable_selector:
              - "code_1"
              - "count"
            comparison_operator: ">"
            value: "5"
    # ELSE 分支不需要配置，通过 sourceHandle: "else" 连接
```

### 比较运算符

| 运算符 | 说明 | 适用类型 |
|--------|------|---------|
| `contains` | 包含 | string |
| `not contains` | 不包含 | string |
| `start with` | 以...开头 | string |
| `end with` | 以...结尾 | string |
| `is` | 等于 | string/number |
| `is not` | 不等于 | string/number |
| `empty` | 为空 | string/array |
| `not empty` | 不为空 | string/array |
| `>` / `>=` / `<` / `<=` | 数值比较 | number |

### 边连接规则

```yaml
# IF 分支（case_1）
- source: "if_else_1"
  sourceHandle: "case_1"
  target: "llm_2"
  targetHandle: "target"

# ELSE IF 分支（case_2）
- source: "if_else_1"
  sourceHandle: "case_2"
  target: "llm_3"
  targetHandle: "target"

# ELSE 分支
- source: "if_else_1"
  sourceHandle: "else"
  target: "output_2"
  targetHandle: "target"
```

---

## 6. HTTP Request 节点

```yaml
- id: "http_1"
  type: "custom"
  position: {x: 638, y: 200}
  data:
    type: "http-request"
    title: "HTTP 请求"
    method: "post"                 # get | post | put | patch | delete | head
    url: "https://api.example.com/data"
    headers: |
      Content-Type: application/json
      Authorization: Bearer {{#env.API_KEY#}}
    params: |
      query: {{#start.query#}}
    body:
      type: "json"                 # json | form-data | x-www-form-urlencoded | raw | binary
      data: |
        {"key": "value", "input": "{{#start.query#}}"}
    timeout:
      connect: 10                  # 连接超时（秒）
      read: 30                     # 读取超时（秒）
      write: 10                    # 写入超时（秒）
    ssl_verify: true
    auth:
      type: "api-key"             # no-auth | api-key
      config:
        type: "bearer"            # basic | bearer | custom
        api_key: "{{#env.API_KEY#}}"
```

### 输出变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `status_code` | number | HTTP 状态码 |
| `body` | string | 响应体 |
| `headers` | object | 响应头 |

---

## 7. Template Transform 节点（模板转换）

```yaml
- id: "template_1"
  type: "custom"
  position: {x: 638, y: 200}
  data:
    type: "template-transform"
    title: "模板转换"
    variables:
      - variable: "title"
        value_selector:
          - "start"
          - "query"
      - variable: "content"
        value_selector:
          - "llm_1"
          - "text"
    template: |
      # {{ title }}
      
      {{ content }}
```

### 输出变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `output` | string | 模板渲染结果 |

---

## 8. Question Classifier 节点（问题分类器）

```yaml
- id: "classifier_1"
  type: "custom"
  position: {x: 334, y: 200}
  data:
    type: "question-classifier"
    title: "问题分类"
    query_variable_selector:
      - "start"
      - "query"
    model:
      provider: "openai"
      name: "gpt-4o"
      mode: "chat"
      completion_params:
        temperature: 0.1
    classes:
      - id: "class_1"
        name: "技术问题"
      - id: "class_2"
        name: "商务咨询"
      - id: "class_3"
        name: "其他"
```

### 边连接规则

```yaml
- source: "classifier_1"
  sourceHandle: "class_1"
  target: "llm_tech"
  targetHandle: "target"
- source: "classifier_1"
  sourceHandle: "class_2"
  target: "llm_biz"
  targetHandle: "target"
```

---

## 9. Parameter Extractor 节点（参数提取器）

```yaml
- id: "extractor_1"
  type: "custom"
  position: {x: 334, y: 200}
  data:
    type: "parameter-extractor"
    title: "参数提取"
    query_variable_selector:
      - "start"
      - "query"
    model:
      provider: "openai"
      name: "gpt-4o"
      mode: "chat"
      completion_params:
        temperature: 0.1
    parameters:
      - name: "platform"
        type: "string"
        description: "社交媒体平台名称"
        required: true
      - name: "tone"
        type: "string"
        description: "语气风格：正式/活泼/专业"
        required: false
    instruction: "从用户输入中提取社交媒体平台和期望的语气风格。"
```

---

## 10. Answer 节点（回答 - Chatflow 终点）

```yaml
- id: "answer"
  type: "custom"
  position: {x: 1550, y: 200}
  data:
    type: "answer"
    title: "回答"
    answer: "{{#llm_1.text#}}"
```

---

## 11. End 节点（输出 - Workflow 终点）

> ⚠️ 节点类型是 `end`（不是 `output`），输出字段是 `outputs`（不是 `variables`），每个输出必须有 `value_type`。

```yaml
- id: '1745000000010'
  type: "custom"
  position: {x: 986, y: 282}
  positionAbsolute: {x: 986, y: 282}
  selected: false
  sourcePosition: right
  targetPosition: left
  width: 242
  height: 103
  data:
    type: "end"                     # ✅ 是 end 不是 output
    title: "输出"
    selected: false
    outputs:                        # ✅ 是 outputs 不是 variables
      - variable: "result"
        value_selector:
          - '1745000000003'
          - text
        value_type: string          # ✅ 必须有 value_type
      - variable: "source"
        value_selector:
          - '1745000000002'
          - result
        value_type: string
```

---

## 12. Variable Assigner 节点（变量赋值）

```yaml
- id: "var_assign_1"
  type: "custom"
  position: {x: 638, y: 200}
  data:
    type: "variable-assigner"
    title: "变量赋值"
    assignments:
      - variable_selector:
          - "conversation"
          - "user_name"
        variable_pool: "conversation"   # conversation | environment
        operation: "overwrite"           # overwrite | set | clear | append | extend | remove_first | remove_last
        set_value: "{{#start.query#}}"
```

### 操作类型

| 操作 | 说明 | 适用类型 |
|------|------|---------|
| `overwrite` | 覆盖写入 | 所有 |
| `set` | 设置值 | string/number/object |
| `clear` | 清空 | array |
| `append` | 追加 | array |
| `extend` | 扩展 | array |
| `remove_first` | 移除首个 | array |
| `remove_last` | 移除末尾 | array |

---

## 13. Variable Aggregator 节点（变量聚合器）

用于合并多个分支的变量：

```yaml
- id: "var_agg_1"
  type: "custom"
  position: {x: 942, y: 200}
  data:
    type: "variable-aggregator"
    title: "变量聚合"
    variables:
      - - "llm_1"
        - "text"
      - - "llm_2"
        - "text"
    output_type: "string"
    advanced_settings:
      group_enabled: false
```

### 输出变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `output` | 由 output_type 决定 | 第一个非空值 |

---

## 14. Iteration 节点（迭代）

> ⚠️ 0.6.0 中迭代节点**不要写** `error_handle_mode`、`is_parallel`、`parallel_nums`、`output_type`（这些是 0.7.0+ 字段）。

### 迭代节点本体

```yaml
- id: '1745000000003'
  type: "custom"
  position: {x: 684, y: 282}
  positionAbsolute: {x: 684, y: 282}
  selected: false
  sourcePosition: right
  targetPosition: left
  width: 1133
  height: 400
  data:
    type: "iteration"
    title: "迭代处理"
    selected: false
    iterator_selector:           # 要迭代的列表变量
      - '1745000000002'          # 上游节点 ID
      - items
    output_selector:             # 每次迭代的输出变量
      - '1745000000008'          # 迭代内最后一个节点 ID
      - result
    start_node_id: '1745000000004'  # 指向 iteration-start 节点
```

### iteration-start 节点（必需！）

迭代节点内部必须有一个专门的 iteration-start 节点：

```yaml
- data:
    isInIteration: true
    iteration_id: '1745000000003'    # 父迭代节点 ID
    selected: false
    title: ''
    type: iteration-start
  draggable: false
  height: 48
  id: '1745000000004'                # start_node_id 指向这里
  parentId: '1745000000003'          # 父迭代节点 ID
  position: {x: 60, y: 104}
  positionAbsolute: {x: 744, y: 386} # 父 position + 子 position
  selectable: false
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom-iteration-start       # ✅ 注意是 custom-iteration-start
  width: 44
  zIndex: 1002
```

### 迭代子节点（必须有的额外字段）

迭代内部的每个节点都需要：

```yaml
- data:
    # ... 正常配置 ...
    isInIteration: true              # ✅ 必需
    isInLoop: false                  # ✅ 必需
    iteration_id: '1745000000003'    # ✅ 必需
  parentId: '1745000000003'          # ✅ 必需（节点层级）
  zIndex: 1002                       # ✅ 必需
  positionAbsolute:                  # ✅ = 父节点 position + 子节点 position
    x: 888                           # 684 + 204
    y: 347                           # 282 + 65
```

### Iteration 边连接规则

```yaml
# 进入迭代（外部边）
- data:
    isInIteration: false
    isInLoop: false
    sourceType: code
    targetType: iteration
  source: '1745000000002'
  sourceHandle: source
  target: '1745000000003'
  targetHandle: target
  zIndex: 0

# 迭代内部：iteration-start → 第一个子节点（内部边）
- data:
    isInIteration: true              # ✅
    isInLoop: false
    iteration_id: '1745000000003'    # ✅
    sourceType: iteration-start
    targetType: code
  source: '1745000000004'            # iteration-start 节点
  sourceHandle: source
  target: '1745000000005'            # 第一个子节点
  targetHandle: target
  zIndex: 1002                       # ✅

# 迭代内部：最后一个子节点 → 迭代节点（关闭循环）
- data:
    isInIteration: true
    isInLoop: false
    iteration_id: '1745000000003'
    sourceType: code
    targetType: iteration
  source: '1745000000008'            # 最后一个子节点
  sourceHandle: source
  target: '1745000000003'            # 迭代节点本身
  targetHandle: output               # ✅ 注意是 output 不是 target
  zIndex: 1002

# 迭代结束输出（外部边）
- data:
    isInIteration: false
    isInLoop: false
    sourceType: iteration
    targetType: code
  source: '1745000000003'
  sourceHandle: source
  target: '1745000000009'
  targetHandle: target
  zIndex: 0
```

---

## 15. List Operator 节点（列表操作）

```yaml
- id: "list_op_1"
  type: "custom"
  position: {x: 638, y: 200}
  data:
    type: "list-operator"
    title: "列表操作"
    variable_selector:
      - "knowledge_1"
      - "result"
    filter:
      enabled: true
      conditions:
        - variable_selector:
            - "item"
            - "score"
          comparison_operator: ">"
          value: "0.5"
    sort:
      enabled: true
      key: "score"
      order: "desc"               # asc | desc
    limit:
      enabled: true
      size: 5
```

---

## 16. Doc Extractor 节点（文档提取器）

```yaml
- id: "doc_extractor_1"
  type: "custom"
  position: {x: 334, y: 200}
  data:
    type: "doc-extractor"
    title: "文档提取"
    variable_selector:
      - "start"
      - "file"
```

### 输出变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `text` | string | 提取的纯文本 |

---

## 17. Agent 节点（智能体）

```yaml
- id: "agent_1"
  type: "custom"
  position: {x: 334, y: 200}
  data:
    type: "agent"
    title: "Agent"
    model:
      provider: "openai"
      name: "gpt-4o"
      mode: "chat"
      completion_params:
        temperature: 0.7
    strategy: "function_calling"    # function_calling | react
    tools: []                       # 工具列表
    max_iteration: 5               # 最大迭代次数
    prompt_template:
      - role: "system"
        text: "你是一个智能助手。"
```

---

## 18. Tool 节点（工具调用）

```yaml
- id: "tool_1"
  type: "custom"
  position: {x: 334, y: 200}
  data:
    type: "tool"
    title: "工具调用"
    provider_id: "google"          # 工具提供商 ID
    provider_type: "builtin"       # builtin | api | workflow | mcp
    tool_name: "google_search"     # 工具名称
    tool_label: "Google 搜索"
    tool_parameters:
      query:
        type: "mixed"
        value: "{{#start.query#}}"
```
