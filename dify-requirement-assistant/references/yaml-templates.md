# Dify 常见工作流 YAML 模板

本文档提供常见工作流场景的完整 DSL YAML 模板，可直接作为生成 YAML 的参考基础。每个模板都是可直接导入 Dify 的完整配置。

## 模板索引

| 模板 | 应用类型 | 场景 | 节点数 |
|------|---------|------|--------|
| [模板1](#模板1知识库问答workflow) | Workflow | 知识库问答（含兜底） | 5 |
| [模板2](#模板2多平台内容生成workflow) | Workflow | 参数提取+批量生成 | 7 |
| [模板3](#模板3智能客服chatflow) | Chatflow | 意图分类+知识库+兜底 | 7 |
| [模板4](#模板4文档分析workflow) | Workflow | 文件上传+提取+分析 | 4 |
| [模板5](#模板5定时报告workflow) | Workflow | HTTP取数+分析+生成 | 5 |
| [模板6](#模板6条件分支处理workflow) | Workflow | 输入校验+分支处理 | 6 |

---

## 模板1：知识库问答（Workflow）

**场景**：用户提问 → 知识库检索 → 判断是否有结果 → 有则LLM回答，无则返回兜底信息。

```yaml
kind: app
version: "0.7.0"
app:
  name: "知识库问答助手"
  description: "基于知识库的智能问答工作流"
  mode: workflow
  icon: "📖"
  icon_background: "#E4FBCC"
  icon_type: emoji

workflow:
  environment_variables: []
  conversation_variables: []
  features:
    retriever_resource:
      enabled: true
  graph:
    nodes:
      - id: "start"
        type: "custom"
        position: {x: 30, y: 200}
        data:
          type: "start"
          title: "开始"
          variables:
            - variable: "query"
              label: "用户问题"
              type: "paragraph"
              required: true
              max_length: 2000

      - id: "knowledge_1"
        type: "custom"
        position: {x: 334, y: 200}
        data:
          type: "knowledge-retrieval"
          title: "知识检索"
          query_variable_selector: ["start", "query"]
          dataset_ids:
            - "YOUR_DATASET_ID"  # TODO: 替换为你的知识库 ID
          retrieval_mode: "multiple"
          multiple_retrieval_config:
            top_k: 3
            score_threshold: 0.5
            score_threshold_enabled: true
            reranking_enable: false

      - id: "if_else_1"
        type: "custom"
        position: {x: 638, y: 200}
        data:
          type: "if-else"
          title: "是否有检索结果"
          cases:
            - case_id: "has_result"
              logical_operator: "and"
              conditions:
                - variable_selector: ["knowledge_1", "result"]
                  comparison_operator: "not empty"
                  value: ""

      - id: "llm_answer"
        type: "custom"
        position: {x: 942, y: 100}
        data:
          type: "llm"
          title: "生成回答"
          model:
            provider: "openai"  # TODO: 按需调整模型提供商
            name: "gpt-4o"     # TODO: 按需调整模型名称
            mode: "chat"
            completion_params:
              temperature: 0.3
              max_tokens: 1000
          prompt_template:
            - role: "system"
              text: "你是一个专业的知识库问答助手。请根据以下检索到的知识内容回答用户问题。如果知识中没有相关信息，请如实告知。回答要准确、简洁。"
            - role: "user"
              text: "检索到的知识：\n{{#knowledge_1.result#}}\n\n用户问题：{{#start.query#}}"
          context:
            enabled: true
            variable_selector: ["knowledge_1", "result"]

      - id: "llm_fallback"
        type: "custom"
        position: {x: 942, y: 300}
        data:
          type: "llm"
          title: "兜底回答"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.7
              max_tokens: 500
          prompt_template:
            - role: "system"
              text: "你是一个友好的助手。知识库中未找到相关信息，请基于自身知识尝试回答用户问题，并告知该信息可能不够准确。"
            - role: "user"
              text: "{{#start.query#}}"

      - id: "var_agg_1"
        type: "custom"
        position: {x: 1246, y: 200}
        data:
          type: "variable-aggregator"
          title: "合并回答"
          variables:
            - ["llm_answer", "text"]
            - ["llm_fallback", "text"]
          output_type: "string"

      - id: "output"
        type: "custom"
        position: {x: 1550, y: 200}
        data:
          type: "output"
          title: "输出"
          variables:
            - variable: "answer"
              value_selector: ["var_agg_1", "output"]
            - variable: "sources"
              value_selector: ["knowledge_1", "result"]

    edges:
      - source: "start"
        sourceHandle: "source"
        target: "knowledge_1"
        targetHandle: "target"
      - source: "knowledge_1"
        sourceHandle: "source"
        target: "if_else_1"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "has_result"
        target: "llm_answer"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "else"
        target: "llm_fallback"
        targetHandle: "target"
      - source: "llm_answer"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "llm_fallback"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "var_agg_1"
        sourceHandle: "source"
        target: "output"
        targetHandle: "target"
    viewport:
      x: 0
      y: 0
      zoom: 0.8

dependencies: []
```

---

## 模板2：多平台内容生成（Workflow）

**场景**：用户输入主题和平台 → 提取参数 → 验证 → LLM分析 → 迭代为每个平台生成内容 → 输出。

```yaml
kind: app
version: "0.7.0"
app:
  name: "多平台内容生成器"
  description: "根据主题为多个平台生成定制内容"
  mode: workflow
  icon: "✍️"
  icon_background: "#D5F5F6"
  icon_type: emoji

workflow:
  environment_variables: []
  conversation_variables: []
  features: {}
  graph:
    nodes:
      - id: "start"
        type: "custom"
        position: {x: 30, y: 200}
        data:
          type: "start"
          title: "开始"
          variables:
            - variable: "topic"
              label: "内容主题"
              type: "paragraph"
              required: true
              max_length: 500
            - variable: "platforms"
              label: "目标平台"
              type: "select"
              options: ["微信", "抖音", "小红书", "微博"]
              required: true

      - id: "extractor_1"
        type: "custom"
        position: {x: 334, y: 200}
        data:
          type: "parameter-extractor"
          title: "提取参数"
          query_variable_selector: ["start", "topic"]
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.1
          parameters:
            - name: "tone"
              type: "string"
              description: "内容语气：正式/活泼/专业/幽默"
              required: true
            - name: "keywords"
              type: "array[string]"
              description: "内容关键词列表"
              required: false
          instruction: "从用户的内容主题中提取语气风格和关键词。"

      - id: "if_else_1"
        type: "custom"
        position: {x: 638, y: 200}
        data:
          type: "if-else"
          title: "参数验证"
          cases:
            - case_id: "valid"
              logical_operator: "and"
              conditions:
                - variable_selector: ["extractor_1", "tone"]
                  comparison_operator: "not empty"
                  value: ""

      - id: "llm_analyze"
        type: "custom"
        position: {x: 942, y: 100}
        data:
          type: "llm"
          title: "内容分析"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.3
              max_tokens: 500
          prompt_template:
            - role: "system"
              text: "你是内容策略专家。分析主题和目标平台，为每个平台生成内容要点。输出 JSON 格式。"
            - role: "user"
              text: "主题：{{#start.topic#}}\n平台：{{#start.platforms#}}\n语气：{{#extractor_1.tone#}}\n关键词：{{#extractor_1.keywords#}}"

      - id: "output_error"
        type: "custom"
        position: {x: 942, y: 300}
        data:
          type: "output"
          title: "错误输出"
          variables:
            - variable: "error"
              value_selector: ["extractor_1", "tone"]

      - id: "output"
        type: "custom"
        position: {x: 1246, y: 100}
        data:
          type: "output"
          title: "输出"
          variables:
            - variable: "analysis"
              value_selector: ["llm_analyze", "text"]

    edges:
      - source: "start"
        sourceHandle: "source"
        target: "extractor_1"
        targetHandle: "target"
      - source: "extractor_1"
        sourceHandle: "source"
        target: "if_else_1"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "valid"
        target: "llm_analyze"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "else"
        target: "output_error"
        targetHandle: "target"
      - source: "llm_analyze"
        sourceHandle: "source"
        target: "output"
        targetHandle: "target"
    viewport:
      x: 0
      y: 0
      zoom: 0.8

dependencies: []
```

---

## 模板3：智能客服（Chatflow）

**场景**：用户消息 → 问题分类 → 技术/商务/其他 → 各分支处理 → 回答。

```yaml
kind: app
version: "0.7.0"
app:
  name: "智能客服助手"
  description: "多意图路由的智能客服对话流"
  mode: advanced-chat
  icon: "🎧"
  icon_background: "#FCEEEF"
  icon_type: emoji

workflow:
  environment_variables: []
  conversation_variables:
    - name: "user_intent"
      value_type: "string"
      value: ""
  features:
    retriever_resource:
      enabled: true
  graph:
    nodes:
      - id: "start"
        type: "custom"
        position: {x: 30, y: 200}
        data:
          type: "start"
          title: "开始"
          variables: []

      - id: "classifier_1"
        type: "custom"
        position: {x: 334, y: 200}
        data:
          type: "question-classifier"
          title: "问题分类"
          query_variable_selector: ["sys", "query"]
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.1
          classes:
            - id: "tech"
              name: "技术问题"
            - id: "business"
              name: "商务咨询"
            - id: "other"
              name: "其他问题"

      - id: "knowledge_tech"
        type: "custom"
        position: {x: 638, y: 100}
        data:
          type: "knowledge-retrieval"
          title: "技术知识库"
          query_variable_selector: ["sys", "query"]
          dataset_ids:
            - "YOUR_TECH_DATASET_ID"  # TODO: 替换为技术知识库 ID
          retrieval_mode: "multiple"
          multiple_retrieval_config:
            top_k: 3
            score_threshold: 0.5
            score_threshold_enabled: true

      - id: "llm_tech"
        type: "custom"
        position: {x: 942, y: 100}
        data:
          type: "llm"
          title: "技术回答"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.3
              max_tokens: 1000
          prompt_template:
            - role: "system"
              text: "你是技术支持专家。根据知识库内容回答用户的技术问题。"
            - role: "user"
              text: "{{#sys.query#}}"
          context:
            enabled: true
            variable_selector: ["knowledge_tech", "result"]
          memory:
            enabled: true
            window:
              enabled: true
              size: 10

      - id: "llm_business"
        type: "custom"
        position: {x: 638, y: 300}
        data:
          type: "llm"
          title: "商务回答"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.5
              max_tokens: 800
          prompt_template:
            - role: "system"
              text: "你是商务顾问。专业、礼貌地回答用户的商务咨询。"
            - role: "user"
              text: "{{#sys.query#}}"
          memory:
            enabled: true
            window:
              enabled: true
              size: 10

      - id: "llm_other"
        type: "custom"
        position: {x: 638, y: 500}
        data:
          type: "llm"
          title: "通用回答"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.7
              max_tokens: 800
          prompt_template:
            - role: "system"
              text: "你是友好的客服助手。尽力回答用户问题，如果无法回答请引导用户联系人工客服。"
            - role: "user"
              text: "{{#sys.query#}}"
          memory:
            enabled: true
            window:
              enabled: true
              size: 10

      - id: "var_agg_1"
        type: "custom"
        position: {x: 1246, y: 300}
        data:
          type: "variable-aggregator"
          title: "合并回答"
          variables:
            - ["llm_tech", "text"]
            - ["llm_business", "text"]
            - ["llm_other", "text"]
          output_type: "string"

      - id: "answer"
        type: "custom"
        position: {x: 1550, y: 300}
        data:
          type: "answer"
          title: "回答"
          answer: "{{#var_agg_1.output#}}"

    edges:
      - source: "start"
        sourceHandle: "source"
        target: "classifier_1"
        targetHandle: "target"
      - source: "classifier_1"
        sourceHandle: "tech"
        target: "knowledge_tech"
        targetHandle: "target"
      - source: "classifier_1"
        sourceHandle: "business"
        target: "llm_business"
        targetHandle: "target"
      - source: "classifier_1"
        sourceHandle: "other"
        target: "llm_other"
        targetHandle: "target"
      - source: "knowledge_tech"
        sourceHandle: "source"
        target: "llm_tech"
        targetHandle: "target"
      - source: "llm_tech"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "llm_business"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "llm_other"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "var_agg_1"
        sourceHandle: "source"
        target: "answer"
        targetHandle: "target"
    viewport:
      x: 0
      y: 0
      zoom: 0.6

dependencies: []
```

---

## 模板4：文档分析（Workflow）

**场景**：用户上传文件 → 提取文本 → LLM 分析 → 结构化输出。

```yaml
kind: app
version: "0.7.0"
app:
  name: "文档分析助手"
  description: "上传文档自动提取关键信息"
  mode: workflow
  icon: "📄"
  icon_background: "#E8F1FF"
  icon_type: emoji

workflow:
  environment_variables: []
  conversation_variables: []
  features:
    file_upload:
      enabled: true
      number_limits: 1
      allowed_file_types: ["document"]
  graph:
    nodes:
      - id: "start"
        type: "custom"
        position: {x: 30, y: 200}
        data:
          type: "start"
          title: "开始"
          variables:
            - variable: "file"
              label: "上传文档"
              type: "file"
              required: true
              allowed_file_types: ["document"]
            - variable: "instruction"
              label: "分析要求"
              type: "paragraph"
              required: false
              max_length: 500

      - id: "doc_extractor_1"
        type: "custom"
        position: {x: 334, y: 200}
        data:
          type: "doc-extractor"
          title: "文档提取"
          variable_selector: ["start", "file"]

      - id: "llm_analyze"
        type: "custom"
        position: {x: 638, y: 200}
        data:
          type: "llm"
          title: "文档分析"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.2
              max_tokens: 2000
          prompt_template:
            - role: "system"
              text: "你是文档分析专家。请仔细阅读文档内容，按照用户要求进行分析，输出结构化的分析结果。"
            - role: "user"
              text: "文档内容：\n{{#doc_extractor_1.text#}}\n\n分析要求：{{#start.instruction#}}"
          structured_output:
            enabled: true
            schema:
              type: "object"
              properties:
                summary:
                  type: "string"
                  description: "文档摘要"
                key_points:
                  type: "array"
                  items:
                    type: "string"
                  description: "关键要点"
                sentiment:
                  type: "string"
                  enum: ["正面", "中性", "负面"]
                  description: "整体情感倾向"

      - id: "output"
        type: "custom"
        position: {x: 942, y: 200}
        data:
          type: "output"
          title: "输出"
          variables:
            - variable: "analysis"
              value_selector: ["llm_analyze", "text"]

    edges:
      - source: "start"
        sourceHandle: "source"
        target: "doc_extractor_1"
        targetHandle: "target"
      - source: "doc_extractor_1"
        sourceHandle: "source"
        target: "llm_analyze"
        targetHandle: "target"
      - source: "llm_analyze"
        sourceHandle: "source"
        target: "output"
        targetHandle: "target"
    viewport:
      x: 0
      y: 0
      zoom: 0.8

dependencies: []
```

---

## 模板5：定时报告（Workflow）

**场景**：HTTP 获取数据 → Code 处理 → LLM 分析 → LLM 生成报告 → 输出。

```yaml
kind: app
version: "0.7.0"
app:
  name: "定时数据报告"
  description: "自动获取数据并生成分析报告"
  mode: workflow
  icon: "📊"
  icon_background: "#FFF6E9"
  icon_type: emoji

workflow:
  environment_variables:
    - name: "API_URL"
      value: "https://api.example.com/data"  # TODO: 替换为你的数据 API
      value_type: "string"
    - name: "API_KEY"
      value: "your-api-key"  # TODO: 替换为你的 API Key
      value_type: "secret"
  conversation_variables: []
  features: {}
  graph:
    nodes:
      - id: "start"
        type: "custom"
        position: {x: 30, y: 200}
        data:
          type: "start"
          title: "开始"
          variables:
            - variable: "report_date"
              label: "报告日期"
              type: "text-input"
              required: false
              max_length: 20

      - id: "http_1"
        type: "custom"
        position: {x: 334, y: 200}
        data:
          type: "http-request"
          title: "获取数据"
          method: "get"
          url: "{{#env.API_URL#}}"
          headers: |
            Authorization: Bearer {{#env.API_KEY#}}
            Content-Type: application/json
          params: |
            date: {{#start.report_date#}}
          body:
            type: "json"
            data: ""
          timeout:
            connect: 10
            read: 30
            write: 10
          ssl_verify: true

      - id: "code_1"
        type: "custom"
        position: {x: 638, y: 200}
        data:
          type: "code"
          title: "数据处理"
          variables:
            - variable: "raw_data"
              value_selector: ["http_1", "body"]
          code_language: "python3"
          code: |
            import json
            
            def main(raw_data: str) -> dict:
                try:
                    data = json.loads(raw_data)
                    # 提取关键指标
                    summary = {
                        "total": data.get("total", 0),
                        "items": len(data.get("items", [])),
                    }
                    return {
                        "summary": json.dumps(summary, ensure_ascii=False),
                        "raw": raw_data[:2000]  # 截断防止过长
                    }
                except Exception as e:
                    return {"summary": f"解析失败: {str(e)}", "raw": raw_data[:2000]}
          outputs:
            summary:
              type: "string"
              children: null
            raw:
              type: "string"
              children: null

      - id: "llm_analyze"
        type: "custom"
        position: {x: 942, y: 200}
        data:
          type: "llm"
          title: "数据分析"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.3
              max_tokens: 1500
          prompt_template:
            - role: "system"
              text: "你是数据分析专家。分析以下数据，找出关键趋势和异常点。"
            - role: "user"
              text: "数据摘要：{{#code_1.summary#}}\n\n原始数据：{{#code_1.raw#}}"

      - id: "llm_report"
        type: "custom"
        position: {x: 1246, y: 200}
        data:
          type: "llm"
          title: "生成报告"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.5
              max_tokens: 2000
          prompt_template:
            - role: "system"
              text: "你是报告撰写专家。根据分析结果生成一份结构化的中文报告，包含：1.数据概览 2.关键发现 3.趋势分析 4.建议措施。使用 Markdown 格式。"
            - role: "user"
              text: "分析结果：{{#llm_analyze.text#}}"

      - id: "output"
        type: "custom"
        position: {x: 1550, y: 200}
        data:
          type: "output"
          title: "输出"
          variables:
            - variable: "report"
              value_selector: ["llm_report", "text"]
            - variable: "data_summary"
              value_selector: ["code_1", "summary"]

    edges:
      - source: "start"
        sourceHandle: "source"
        target: "http_1"
        targetHandle: "target"
      - source: "http_1"
        sourceHandle: "source"
        target: "code_1"
        targetHandle: "target"
      - source: "code_1"
        sourceHandle: "source"
        target: "llm_analyze"
        targetHandle: "target"
      - source: "llm_analyze"
        sourceHandle: "source"
        target: "llm_report"
        targetHandle: "target"
      - source: "llm_report"
        sourceHandle: "source"
        target: "output"
        targetHandle: "target"
    viewport:
      x: 0
      y: 0
      zoom: 0.7

dependencies: []
```

---

## 模板6：条件分支处理（Workflow）

**场景**：用户输入 → LLM 提取意图 → IF/ELSE 分支（不同意图不同处理）→ 合并输出。

```yaml
kind: app
version: "0.7.0"
app:
  name: "意图路由处理"
  description: "根据用户意图路由到不同处理流程"
  mode: workflow
  icon: "🔀"
  icon_background: "#F0F0FF"
  icon_type: emoji

workflow:
  environment_variables: []
  conversation_variables: []
  features: {}
  graph:
    nodes:
      - id: "start"
        type: "custom"
        position: {x: 30, y: 200}
        data:
          type: "start"
          title: "开始"
          variables:
            - variable: "query"
              label: "用户输入"
              type: "paragraph"
              required: true
              max_length: 1000

      - id: "llm_classify"
        type: "custom"
        position: {x: 334, y: 200}
        data:
          type: "llm"
          title: "意图识别"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.1
              max_tokens: 50
          prompt_template:
            - role: "system"
              text: "你是意图分类器。将用户输入分类为以下之一：SUMMARY（摘要）、TRANSLATE（翻译）、ANALYZE（分析）。只输出分类结果，不要其他内容。"
            - role: "user"
              text: "{{#start.query#}}"
          structured_output:
            enabled: true
            schema:
              type: "object"
              properties:
                intent:
                  type: "string"
                  enum: ["SUMMARY", "TRANSLATE", "ANALYZE"]

      - id: "if_else_1"
        type: "custom"
        position: {x: 638, y: 200}
        data:
          type: "if-else"
          title: "意图路由"
          cases:
            - case_id: "summary"
              logical_operator: "and"
              conditions:
                - variable_selector: ["llm_classify", "text"]
                  comparison_operator: "contains"
                  value: "SUMMARY"
            - case_id: "translate"
              logical_operator: "and"
              conditions:
                - variable_selector: ["llm_classify", "text"]
                  comparison_operator: "contains"
                  value: "TRANSLATE"

      - id: "llm_summary"
        type: "custom"
        position: {x: 942, y: 100}
        data:
          type: "llm"
          title: "摘要生成"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.3
              max_tokens: 500
          prompt_template:
            - role: "system"
              text: "请将以下内容生成简洁摘要，不超过200字。"
            - role: "user"
              text: "{{#start.query#}}"

      - id: "llm_translate"
        type: "custom"
        position: {x: 942, y: 300}
        data:
          type: "llm"
          title: "翻译"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.3
              max_tokens: 1000
          prompt_template:
            - role: "system"
              text: "请将以下内容翻译为英文。"
            - role: "user"
              text: "{{#start.query#}}"

      - id: "llm_analyze"
        type: "custom"
        position: {x: 942, y: 500}
        data:
          type: "llm"
          title: "分析"
          model:
            provider: "openai"
            name: "gpt-4o"
            mode: "chat"
            completion_params:
              temperature: 0.5
              max_tokens: 1000
          prompt_template:
            - role: "system"
              text: "请分析以下内容，给出关键信息、情感倾向和主题。"
            - role: "user"
              text: "{{#start.query#}}"

      - id: "var_agg_1"
        type: "custom"
        position: {x: 1246, y: 300}
        data:
          type: "variable-aggregator"
          title: "合并结果"
          variables:
            - ["llm_summary", "text"]
            - ["llm_translate", "text"]
            - ["llm_analyze", "text"]
          output_type: "string"

      - id: "output"
        type: "custom"
        position: {x: 1550, y: 300}
        data:
          type: "output"
          title: "输出"
          variables:
            - variable: "result"
              value_selector: ["var_agg_1", "output"]

    edges:
      - source: "start"
        sourceHandle: "source"
        target: "llm_classify"
        targetHandle: "target"
      - source: "llm_classify"
        sourceHandle: "source"
        target: "if_else_1"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "summary"
        target: "llm_summary"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "translate"
        target: "llm_translate"
        targetHandle: "target"
      - source: "if_else_1"
        sourceHandle: "else"
        target: "llm_analyze"
        targetHandle: "target"
      - source: "llm_summary"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "llm_translate"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "llm_analyze"
        sourceHandle: "source"
        target: "var_agg_1"
        targetHandle: "target"
      - source: "var_agg_1"
        sourceHandle: "source"
        target: "output"
        targetHandle: "target"
    viewport:
      x: 0
      y: 0
      zoom: 0.6

dependencies: []
```

---

## 使用说明

1. **选择模板**：根据用户需求场景选择最接近的模板作为基础
2. **修改适配**：根据具体需求调整节点配置、提示词、变量
3. **替换占位符**：将所有 `YOUR_*_ID` 和 `TODO` 标注的占位符替换为实际值
4. **调整模型**：根据用户偏好调整 `provider` 和 `name`
5. **验证完整性**：对照 `dsl-format.md` 中的检查清单验证 YAML
