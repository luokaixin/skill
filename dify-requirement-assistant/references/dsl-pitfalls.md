# Dify DSL 0.6.0 避坑指南

本文档记录了在实际生成 Dify DSL YAML 时踩过的坑，每个条目都来自真实的导入失败案例。

## 致命错误（直接导致导入失败）

### 1. Output 节点类型错误

**错误写法**（0.7.0+ 才支持）：
```yaml
data:
  type: output        # ❌ 错误！
  variables:          # ❌ 错误！
    - variable: result
      value_selector: [llm_1, text]
```

**正确写法**（0.6.0）：
```yaml
data:
  type: end           # ✅ 正确
  outputs:            # ✅ 用 outputs 不是 variables
    - variable: result
      value_selector: [llm_1, text]
      value_type: string  # ✅ 必须有 value_type
```

### 2. LLM structured_output 不支持

**错误写法**（0.7.0+ 功能）：
```yaml
data:
  type: llm
  structured_output:          # ❌ 0.6.0 不支持此字段
    schema:
      type: object
      properties:
        result:
          type: string
  structured_output_enabled: true  # ❌ 必须为 false 或不写
```

**正确写法**（0.6.0）：
```yaml
data:
  type: llm
  structured_output_enabled: false  # ✅ 设为 false
  # 不写 structured_output 字块
  # 如需结构化输出，在 prompt 中要求模型输出 JSON，再用 Code 节点解析
```

### 3. 迭代节点 0.7.0+ 字段

**错误写法**：
```yaml
data:
  type: iteration
  error_handle_mode: terminated  # ❌ 0.7.0+
  is_parallel: false             # ❌ 0.7.0+
  parallel_nums: 10              # ❌ 0.7.0+
  output_type: array[string]     # ❌ 0.7.0+
```

**正确写法**（0.6.0）：
```yaml
data:
  type: iteration
  iterator_selector: [code_1, items]
  output_selector: [code_inner, result]
  start_node_id: '1745000000004'  # 指向 iteration-start 节点
  # 不要写 error_handle_mode, is_parallel, parallel_nums, output_type
```

### 4. dependencies 不能为空数组

**错误写法**：
```yaml
dependencies: []  # ❌ 空数组可能导致导入失败
```

**正确写法**：需要列出用到的插件依赖：
```yaml
dependencies:
  - current_identifier: null
    type: package
    value:
      plugin_unique_identifier: langgenius/deepseek-4399:0.0.15@xxxxx
      version: null
```

> **最佳实践**：从用户环境中导出一个工作流 YAML，复制其 dependencies 部分。

### 5. 节点 ID 必须是纯数字字符串

**错误写法**：
```yaml
- id: start              # ❌ 语义化命名
- id: llm_analyze        # ❌
- id: code_prepare       # ❌
```

**正确写法**：
```yaml
- id: '1745000000001'   # ✅ 纯数字字符串
- id: '1745000000002'   # ✅
```

> Dify 导出时 ID 是时间戳格式的数字字符串，导入时也期望此格式。

### 6. 知识库 dataset_ids 不能用占位符

**错误写法**：
```yaml
dataset_ids:
  - YOUR_DATASET_ID  # ❌ 导入时可能校验失败
```

**正确写法**：使用一个真实的 dataset_id（导入后用户手动替换），或在导入说明中告知用户先导入再手动配置。

---

## 结构缺失错误（导致解析异常）

### 7. 节点缺少必需字段

每个节点（包括 iteration-start）都必须有以下字段：

```yaml
- data: { ... }
  height: 116            # ✅ 必需
  id: '1745000000001'    # ✅ 必需
  position:              # ✅ 必需
    x: 80
    y: 282
  positionAbsolute:      # ✅ 必需
    x: 80
    y: 282
  selected: false        # ✅ 必需
  sourcePosition: right  # ✅ 必需
  targetPosition: left   # ✅ 必需
  type: custom           # ✅ 必需
  width: 242             # ✅ 必需
```

### 8. 边缺少必需字段

每条边都必须有：

```yaml
- data:                              # ✅ 必需
    isInIteration: false             # ✅ 必需
    isInLoop: false                  # ✅ 必需
    sourceType: start                # ✅ 必需
    targetType: code                 # ✅ 必需
  id: 'xxx-source-yyy-target'       # ✅ 必需
  source: '1745000000001'            # ✅ 必需
  sourceHandle: source               # ✅ 必需
  target: '1745000000002'            # ✅ 必需
  targetHandle: target               # ✅ 必需
  type: custom                       # ✅ 必需
  zIndex: 0                          # ✅ 必需
```

### 9. 迭代节点内部结构缺失

迭代节点需要一个专门的 `iteration-start` 节点：

```yaml
# iteration-start 节点（必需！）
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
  positionAbsolute: {x: 744, y: 386}
  selectable: false
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom-iteration-start       # ✅ 注意：是 custom-iteration-start
  width: 44
  zIndex: 1002
```

迭代子节点必须有的额外字段：
```yaml
- data:
    isInIteration: true              # ✅ 必需
    isInLoop: false                  # ✅ 必需
    iteration_id: '1745000000003'    # ✅ 必需
  parentId: '1745000000003'          # ✅ 必需（节点层级）
  zIndex: 1002                       # ✅ 必需
```

迭代内部边的额外字段：
```yaml
- data:
    isInIteration: true              # ✅ 必需
    iteration_id: '1745000000003'    # ✅ 必需
  zIndex: 1002                       # ✅ 必需
```

### 10. positionAbsolute 计算

迭代子节点的 `positionAbsolute` = 父节点 position + 子节点 position：

```
父节点 position: {x: 684, y: 282}
子节点 position: {x: 204, y: 65}
子节点 positionAbsolute: {x: 888, y: 347}  # 684+204, 282+65
```

---

## 字段值错误（导致功能异常）

### 11. Start 变量不要写 max_length

**错误写法**：
```yaml
variables:
  - variable: query
    type: text-input
    max_length: 256    # ❌ 0.6.0 不需要
```

**正确写法**：
```yaml
variables:
  - default: ''
    hint: ''
    label: query
    options: []
    placeholder: ''
    required: true
    type: text-input
    variable: query
```

### 12. LLM 节点不要写 memory（Workflow 模式）

Workflow 模式下 LLM 节点不需要 `memory` 字段。只有 Chatflow 模式才需要。

### 13. 知识检索不要写 score_threshold

**0.6.0 中 `multiple_retrieval_config` 的正确字段**：
```yaml
multiple_retrieval_config:
  reranking_enable: true
  reranking_mode: reranking_model
  reranking_model:
    model: qwen3-vl-rerank
    provider: langgenius/tongyi-4399/tongyi
  top_k: 4
  # ❌ 不要写 score_threshold
  # ❌ 不要写 score_threshold_enabled
```

### 14. 知识检索必须有 query_attachment_selector

```yaml
query_attachment_selector: []  # ✅ 必需，即使为空
```

### 15. features.file_upload 必须完整

```yaml
file_upload:
  allowed_file_extensions: [.JPG, .JPEG, .PNG, .GIF, .WEBP, .SVG]
  allowed_file_types: [image]
  allowed_file_upload_methods: [local_file, remote_url]
  enabled: false
  fileUploadConfig:                    # ✅ 必需
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
  image:                               # ✅ 必需
    enabled: false
    number_limits: 3
    transfer_methods: [local_file, remote_url]
  number_limits: 3
```

### 16. workflow 必须有 rag_pipeline_variables

```yaml
workflow:
  # ... 其他字段
  rag_pipeline_variables: []  # ✅ 必需，即使为空
```

---

## 模型配置注意事项

### 17. provider 格式

provider 不是简单的 `openai`，而是完整路径：

```yaml
model:
  provider: langgenius/deepseek-4399/deepseek    # ✅ 完整路径
  name: deepseek-v4-pro
  mode: chat
  completion_params:
    temperature: 0.7
```

常见 provider 值（取决于用户环境安装的插件）：
- `langgenius/deepseek-4399/deepseek`
- `langgenius/openai-4399/openai`
- `langgenius/tongyi-4399/tongyi`

> **最佳实践**：询问用户使用的模型，或从用户导出的 YAML 中复制 provider 值。

### 18. Code 节点变量必须有 value_type

```yaml
variables:
  - value_selector: [start, query]
    value_type: string    # ✅ 必需
    variable: input_text
```

### 19. prompt_template 每个 item 必须有 id

```yaml
prompt_template:
  - id: <uuid>        # ✅ 必需，使用 UUID
    role: system
    text: '...'
  - id: <uuid>        # ✅ 必需
    role: user
    text: '...'
```

---

## 生成 YAML 的黄金法则

1. **先找一个能用的 YAML 作为参照**：从用户环境中导出一个简单的工作流，作为格式基准
2. **用 Python 脚本生成**：用 `yaml.dump()` 而非手写，避免缩进和格式问题
3. **生成后做对比验证**：和参照 YAML 逐字段对比，确保所有必需字段都存在
4. **不要使用 0.7.0+ 功能**：`structured_output`、`error_handle_mode`、`output_type` 等都不兼容
5. **节点 ID 用数字字符串**：不要用语义化命名
6. **Code 节点代码必须带中文注释**：用户可能不懂代码，每一步都要用 `#` 注释说明在做什么。注释规范：
   - 每个关键步骤前加 `# 序号. 做什么` 的注释
   - 对不直观的代码行加行尾注释
   - 对 try/except 等兜底逻辑说明触发条件和默认行为
   - 对 return 语句说明每个输出字段的含义
