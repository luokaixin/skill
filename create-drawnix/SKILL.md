---
name: create-drawnix
description: >-
  生成可被 drawnix 导入并继续编辑的白板 JSON（顶层 cells）。用户要画流程图、思维导图、树状图、时间线、里程碑、增长飞轮、环形图、循环图、蜂巢图、雷达图、金字塔、泳道图、时序图、组织架构图、鱼骨图、UML、ER、四象限、表格、分区或便签，或提到 drawnix、白板、画板、导入 JSON、shape-*、pen-stroke、table-node、topic 树边、照着参考图复刻时必须使用。批量生成见 references/builder-workflow.md；按参考图复刻的像素验收见 references/visual-verification.md；按图形骨架选型见 references/index.md；配色与版式规范见 references/design-system.md。
---

# drawnix 白板 JSON 生成

把一段需求（或一张参考图）转换成一个**可直接导入、并且导入后仍能继续编辑**的 drawnix 白板 JSON。

核心目标不是「画出一张图」，而是「画出一张**别人能接着改**的图」。判断标准只有一条：

> 用户能否在编辑器里单独选中、单独修改每一段文字、每一个框、每一条线？

如果做不到，即使视觉上完全正确，也不是合格产出。

## 交付形态

| 项目 | 说明 |
| --- | --- |
| 格式 | 单个 **JSON 文件**（UTF-8，扩展名 `.json`） |
| 结构 | 根对象只有一个 `cells` 数组：`{ "cells": [ ... ] }` |
| 用途 | 编辑器「导入 JSON」；或作为模板源文件 |
| **不是** | 图片、PDF、`.drawio`、带注释的 JSON、Markdown 围栏里的片段 |

## 开始之前

1. 读完本文件。
2. 判断这是哪种任务，读对应文档：

| 任务 | 先读 |
| --- | --- |
| 要批量产出，或新建一套模板 | [references/builder-workflow.md](references/builder-workflow.md) —— 用脚本生成 + 断言校验，**不要手写 JSON** |
| 有参考图要照着做 | [references/visual-verification.md](references/visual-verification.md) —— 像素级测量与验收 |
| 不确定该用哪种图 | [references/index.md](references/index.md) —— 按「图形骨架」选型 |
| 要控制配色与版式风格 | [references/design-system.md](references/design-system.md) |

3. 只输出一个 JSON 对象作为正文，不加注释、不加尾逗号、不加 Markdown 围栏（除非明确要求解释）。

---

## 一、基本契约

1. 顶层必须是 `cells` 数组。
2. 每个节点/边有唯一字符串 `id`。边通过 `source.cell` / `target.cell` 引用节点 `id`，**不引用节点对象**。
3. 节点必须有 `shape`、`position`、`size`。只使用已注册的 `shape` 值，不要自创名称。
4. 颜色统一用 `#RRGGBB`；透明度用 `fillOpacity` / `strokeOpacity`；虚线用 `strokeDasharray`。
5. 不要写 UI 相关字段（`view`、`tools`、`attrs.selection`、`attrs.hover`、`attrs.collapse` 等）。
6. 多行文字用 `attrs.label.html`（如 `<div>第一行</div><div>第二行</div>`），不要依赖 `\n`。
7. 手动尺寸标记：
   - `shape` 以 `shape-` 开头的图形 → `data.manualResized: true`
   - `text-node` → `data.textManualResized: true`
   - `topic` / `sticky-node` / `table-node` / `image-node` / `pen-stroke` / `section` / `group` / `edge` → 两个都**不写**

   字段写在 `data` 里，不是 `attrs`。已有 `data` 时只合并，不覆盖。

最小可用示例：

```json
{
  "cells": [
    {
      "id": "n1",
      "shape": "shape-rounded-rect",
      "position": { "x": 100, "y": 100 },
      "size": { "width": 120, "height": 80 },
      "attrs": { "label": { "text": "开始" } }
    }
  ]
}
```

`shape-*` 的默认背景、边框、文字颜色会由形状配置补齐，不需要手写样式。

---

## 二、字号规则

**只允许 12 / 14 / 16 / 18 / 20 及更大的标题字号。禁止 9 / 10 / 11 / 13 / 15 / 17 / 19。**

| 字号 | 用途 |
| --- | --- |
| 14 | 正文默认：流程节点、表格单元格、说明文字 |
| 12 | 仅拥挤处的辅助信息：图例、角标、密集表格次要列 |
| 16–20 | 卡片标题、分区标题、表头、关键数字 |

为什么要卡死：13 这类值通常是「14 略大、12 略小」时随手写的，结果同一张图里出现 12/13/14 三种接近却不等比的字号，视觉上参差。要么 14，要么 12，不要中间态。

配套约束：

- 调字号后若节点宽度不足，必须同步加宽 `size.width` 或拆分文本，不能让文字溢出或被挤压换行。
- 表格类节点还要同步更新 `tableStyle.fontSize`。
- 12px 的文字面积占比不要超过约 20%，内容多时优先放大画布或拆分布局，不要靠缩字号硬塞。
- 校验必须是**白名单**，不能写成 `fontSize < 12` —— 下限判断会放过 13/15/17。

---

## 三、节点类型

### 3.1 特殊节点

| `shape` | 用途 | 必需内容字段 | 备注 |
| --- | --- | --- | --- |
| `topic` | 思维导图 / 树状图 / 主题树节点 | `attrs.label.text`、`data.layout`、`data.isRoot` | 根与子节点共用 |
| `text-node` | 纯文本 | `attrs.label.text` | 导入时以 `size` 为准，需留足 |
| `sticky-node` | 便签 | `attrs.label.text`、`attrs.body.fill` | 默认 220×220，正文 20px |
| `table-node` | 表格 / 泳道 / 类框 / ER / 组合片段 | `data.cells` 等 | 见 3.4 |
| `image-node` | 图片 | `data.src` | 支持 data URL 或可访问 URL |
| `pen-stroke` | 手绘路径 / 任意多边形 | `attrs.penPath.d`、`data.points` | 路径坐标相对节点左上角 |
| `section` | 分区 | `data.title`、`attrs.label.text` | 空间容器，坐标为绝对值 |
| `group` | 成组容器 | `children` | 透明 AABB，本身不绘制内容 |
| `shape-*` | 基础图形 / 流程图图元 | `attrs.label.text`（可选） | 外观由形状配置补齐 |

### 3.2 常用 `shape-*`

| 分类 | 形状名 |
| --- | --- |
| 基础 | `shape-rect`、`shape-rounded-rect`、`shape-full-rounded-rect`、`shape-circle`、`shape-diamond`、`shape-triangle`、`shape-trapezoid`、`shape-parallelogram`、`shape-hexagon`、`shape-pentagon`、`shape-octagon`、`shape-cylinder`、`shape-cloud`、`shape-star`、`shape-cross`、`shape-circular-ring`、`shape-pie`、`shape-cube` |
| 箭头 | `shape-arrow-left`、`shape-arrow-right`、`shape-arrow-both`、`shape-right-triangle` |
| 标注 | `shape-callout-rounded`、`shape-callout-ellipse`、`shape-brace-left`、`shape-brace-right` |
| 阶梯 | `shape-step-concave`、`shape-step-flat` |
| 流程图 | `shape-flow`、`shape-start-end`、`shape-judge`、`shape-data`、`shape-database`、`shape-document`、`shape-manual-input`、`shape-manual-operation`、`shape-delay`、`shape-prepare`、`shape-queue`、`shape-predefined-process`、`shape-off-page-connector` |
| 数据流图 | `shape-external-entity`、`shape-data-processing`、`shape-data-processing-circle`、`shape-data-store` |
| 组件图 | `shape-component`、`shape-component2`、`shape-component-interface`、`shape-component-assembly` |
| 状态图 | `shape-state-start`、`shape-state-end`、`shape-state-concurrency` |
| 类图 | `shape-simple-class`、`shape-category`、`shape-annotation` |
| 时序图 | `shape-actor`、`shape-lifecycle` 等 |

常用默认尺寸（生成时应显式写 `size`，不要依赖默认值）：

| 形状 | 宽 × 高 |
| --- | --- |
| `shape-rounded-rect` / `shape-rect` / `shape-flow` | 120 × 80 |
| `shape-full-rounded-rect` / `shape-start-end` / `shape-document` | 120 × 80 |
| `shape-diamond` / `shape-cylinder` | 100 × 100 |
| `shape-circle` | 80 × 80 |
| `shape-circular-ring` / `shape-pie` | 110 × 110 |
| `shape-cube` | 148 × 106 |
| `shape-component` / `shape-component2` | 160 × 100 |

### 3.3 四个形状陷阱（都会造成「看不出来」的错误）

这几条的共同特点：**从 JSON 字段上看完全正常，但渲染出来不对**。只能靠形状名称的正确用法规避。

#### 陷阱 1：全圆角矩形不能用 `rx = 高度/2` 冒充

`rx` 是**普通圆角矩形**的参数，渲染时会对它做上限裁剪。一旦裁剪，两端就不再是半圆，
退回普通圆角矩形 —— 而 JSON 里 `rx` 的值确实等于 `h/2`，看不出问题。

```json
// ✗ 错：看着对，渲染出来不是胶囊
{ "shape": "shape-rounded-rect", "attrs": { "body": { "rx": 17, "ry": 17 } } }

// ✓ 对：形状类型本身保证两端是完整半圆
{ "shape": "shape-full-rounded-rect" }
```

**判据**：检查 `shape` 字段必须是 `shape-full-rounded-rect`。

#### 陷阱 2：六边形的朝向不可控

`shape-hexagon` 的朝向（平顶 / 尖顶）和斜边内缩量由渲染实现决定，JSON 里没有参数可调。

| 朝向 | 特征 | 适用 |
| --- | --- | --- |
| 平顶 | 上下是水平边，左右是尖角 | 蜂巢拼接**必须**用这个 |
| 尖顶 | 上下是尖角，左右是竖直边 | 蜂窝拼不上 |

需要精确朝向时，用 6 顶点闭合 `pen-stroke` 自己画：

```python
k = w * 0.25
x0, x1, y0, y1 = cx - w/2, cx + w/2, cy - h/2, cy + h/2
pts = [(x0+k, y0), (x1-k, y0), (x1, cy), (x1-k, y1), (x0+k, y1), (x0, cy)]
```

并断言「最上面一行有两个不同的 x」（存在水平边）：

```python
top_y = min(p["y"] for p in pts)
assert len([p for p in pts if abs(p["y"] - top_y) < 0.01]) == 2, "尖顶六边形"
```

#### 陷阱 3：弧 / 环不能用粗描边画

把 `pen-stroke` 的 `strokeWidth` 设成环厚，看起来能得到环带，但**每段折线是独立矩形**，
拐角处 `linejoin` 表现不稳 → 锯齿 + 接缝，环看起来是碎的。

**正解**：外弧正向采样 + 内弧反向采样 + `Z` 闭合成**一整块实心面**，
`fill` 填色、`strokeWidth: 0`。详见 [builder-workflow.md](references/builder-workflow.md) §5。

#### 陷阱 4：任何背景色形状压在环带上都会挖洞

环带范围内出现任何白色形状（箭头挖槽、装饰覆盖、内部缺口），就会在环上啃出一个洞，
视觉上环被劈成两截。三种常见错法：

| 错法 | 症状 |
| --- | --- |
| 环留缺口、再用箭头补 | 缺口两侧环端总有一处露白缝 |
| 环完整 + 白色燕尾槽压在环带正中 | 白槽横贯环带，环被劈开 |
| 环完整 + 白槽够深够宽 | 直接挖穿环带 |

**正解**：箭头做成**一个轮廓自带内凹的实心多边形**（与环同色），全程不用白色形状。
自检要逐度扫描环带：

```python
holes = [d for d in range(360) if not band_has_fill(d)]
assert not holes, f"环在 {holes} 度被挖洞"
```

### 3.4 `table-node`

表格的 `size` 应等于 `colWidths` 之和 × `rowHeights` 之和。需要固定行高时把该行
`rowDragged` 写成 `true`（组合片段首行保持 `false`），否则行高会按内容自适应。

**网格类布局最易踩的坑：格子高度必须一致。**

`table-node` 的高度由自己的 `rowHeights` 之和决定。若各格行数不同（左上 3 条、左下 2 条），
实际高度就不同，而坐标仍按统一 `Q_H` 推算，于是出现：中间空出一段、上下排下沿不齐、轴标签悬空。

```python
HEAD_H, ROW_H, ROWS = 46, 46, 5
Q_H = HEAD_H + ROW_H * ROWS          # 高度由行数反算，不预设
rows = [[title]] + [[t] for t in items] + [[""] for _ in range(ROWS - len(items))]
```

空行铺成**等高空行**，不要用一条超高填充行代替（那样看起来是一整块色块，不像表格）。

---

## 四、连线

### 4.1 两类连线

| 类型 | 判定 | 用途 | 参与树布局 |
| --- | --- | --- | --- |
| 树边 | **没有** `data.lineType` | 思维导图 / 树 / 主题树的父子关系 | 是 |
| 普通连接线 | `data.lineType` 为 `line` / `line-arrow` / `polyline` / `curve` | 流程图、类图、任意节点间连线 | 否 |

普通连接线**必须**写 `data.lineType`。漏写会被当成树边：两端是 `topic` 时会破坏树结构，
并且不进入连接线的选中/编辑逻辑。

### 4.2 端点必须绑定节点（最重要的一条）

```json
{
  "cell": "node-id",
  "anchor": { "name": "right", "args": { "rotate": true } },
  "connectionPoint": { "name": "shape-boundary", "args": { "side": "right" } }
}
```

| 字段 | 含义 |
| --- | --- |
| `anchor.name` | `top` / `right` / `bottom` / `left` |
| `anchor.args.rotate` | 节点旋转后连接点是否跟随，建议 `true` |
| `connectionPoint.name` | `anchor` 取包围盒边中点；`shape-boundary` 取真实外轮廓交点 |
| `connectionPoint.args.side` | 必须与 `anchor.name` 相同 |

选择建议：

- 矩形类、`table-node`、`text-node`、`topic` → `connectionPoint: { "name": "anchor" }`
- 不规则图形（菱形、圆、箭头、手绘）→ `shape-boundary`，避免线停在包围盒空白处
- 不确定时统一用 `shape-boundary` 也安全，没有外轮廓的形状会自动退回锚点

### 4.3 不要使用自由端点

自由端点写作 `{ "x": 700, "y": 500 }`，没有 `cell`。

**问题**：节点的 `position` 会被精确保留，而自由端点需要渲染器自行解释，是唯一会被二次换算的东西。
实测结果是所有自由端点连线**整体平移**，节点位置完全正确而箭头全部跑偏 —— 看起来像「箭头和文字脱节」，
其实文字是对的，错的是线。

**规则**：

1. 能用 `source.cell` / `target.cell` 绑定的，一律绑定。
2. 不要用 `vertices` 补偿漂移 —— `vertices` 同样是自由坐标，会跟着一起漂。
3. 不要用细长矩形假造连线：拖动节点不跟随、不能重新布线、没有箭头语义、导出到其它工具只是一堆矩形。
   **连线必须是 `shape: "edge"`。**

**需要「线端落在精确位置、但那里没有节点」时**，放一个 `1×1` 隐形锚点：

```json
{
  "id": "pt-1",
  "shape": "shape-rect",
  "position": { "x": 312, "y": 279.5 },
  "size": { "width": 1, "height": 1 },
  "attrs": { "body": { "fill": "none", "stroke": "none", "strokeWidth": 0 } },
  "data": { "manualResized": true },
  "zIndex": 0
}
```

要点：

- `fill: none` + `stroke: none`，用户看不到也点不中；`zIndex: 0` 压最底层
- 不要写 `attrs.label`（否则渲染出「输入文本」占位）
- 连线的 `connectionPoint` 用 `{ "name": "anchor" }`
- **对齐方向要算准**：`left` 取 `x`，`right` 取 `x + 1`，`top` 取 `y`，`bottom` 取 `y + 1`。
  1×1 的盒子无法让 left 和 right 同时精确，所以**一个锚点只服务一个方向**

**锚点要严格限量（每张图 ≤ 10 个）。** 锚点是空壳节点，数量一多，
在导入 / 复制 / 导出链路里容易被当空对象清理，挂在上面的边会被整条丢弃 ——
表现为「一部分连线凭空消失」，且没有任何报错。

优先换布局让两端自然对齐到节点边中点，而不是继续堆锚点。**布局让位给可靠性。**

### 4.4 连线类型与端点装饰

| `data.lineType` | `connector` | 默认端点 | 说明 |
| --- | --- | --- | --- |
| `line` | `{ "name": "arrow-line" }` | 无箭头 | 直线 |
| `line-arrow` | `{ "name": "arrow-line" }` | 终点三角箭头 | 直线 + 箭头 |
| `polyline` | `{ "name": "arrow-polyline", "args": { "radius": 8 } }` | 终点三角箭头 | 正交折线，无拐点时自动避障 |
| `curve` | `{ "name": "arrow-curve" }` | 终点三角箭头 | 三次贝塞尔 |

端点装饰写在边 `data` 上的 `startCap` / `endCap`，取值 1–15：

| 值 | 含义 | 值 | 含义 |
| --- | --- | --- | --- |
| 1 | 无 | 9 | 圆环 |
| 2 | 箭头 | 10 | 十字 |
| 3 | 三角箭头 | 11 | 开放箭头 |
| 4 | 空心三角 | 12 | 分叉箭头 |
| 5 | 燕尾箭头 | 13 | 双线 |
| 6 | 空心菱形 | 14 | 环形箭头 |
| 7 | 圆点 | 15 | 圆环竖线 |
| 8 | 叉号 | | |

默认 `startCap = 1`；`endCap` 在 `line` 类型为 1，其余为 3。

完整连线示例：

```json
{
  "id": "edge-1",
  "shape": "edge",
  "source": {
    "cell": "a",
    "anchor": { "name": "right", "args": { "rotate": true } },
    "connectionPoint": { "name": "shape-boundary", "args": { "side": "right" } }
  },
  "target": {
    "cell": "b",
    "anchor": { "name": "left", "args": { "rotate": true } },
    "connectionPoint": { "name": "shape-boundary", "args": { "side": "left" } }
  },
  "connector": { "name": "arrow-line" },
  "attrs": { "line": { "stroke": "#A2B1C3", "strokeWidth": 2,
                       "strokeOpacity": 1, "targetMarker": null } },
  "data": { "lineType": "line-arrow", "startCap": 1, "endCap": 3 },
  "zIndex": 10
}
```

无论是否需要箭头，都建议在 `attrs.line` 里写 `targetMarker: null`，避免残留默认箭头。

### 4.5 树边

```json
{
  "id": "tree-1",
  "shape": "edge",
  "source": { "cell": "parent", "anchor": { "name": "right", "args": { "rotate": true } },
              "connectionPoint": { "name": "anchor" } },
  "target": { "cell": "child", "anchor": { "name": "left", "args": { "rotate": true } },
              "connectionPoint": { "name": "anchor" } },
  "connector": { "name": "topic-stub", "args": { "stub": 30 } },
  "attrs": { "line": { "stroke": "#3F6AFC", "strokeWidth": 2, "strokeOpacity": 1,
                       "strokeDasharray": "none", "targetMarker": null } },
  "data": { "topicOrder": 0 },
  "zIndex": 1
}
```

规则：

- 树边**不写** `data.lineType`
- 必须写 `attrs.line.targetMarker = null`，否则默认箭头会出现在思维导图线上
- `data.topicOrder` 是同一父节点下的兄弟顺序，从 0 开始
- 树状图「根 → 子节点」用 `connector: { "name": "rounded" }`，并建议写一个 L 形拐点：
  `vertices: [{ "x": 根中心x, "y": 子节点中心y }]`；分支内部继续用 `topic-stub`

### 4.6 类图关系

| 关系 | `lineType` | `startCap` | `endCap` | 虚线 |
| --- | --- | --- | --- | --- |
| 关联 | `line` | 1 | 1 | 否 |
| 有向关联 | `line-arrow` | 1 | 3 | 否 |
| 聚合 | `line-arrow` | 1 | 6 | 否 |
| 组合 | `line-arrow` | 1 | 5 | 否 |
| 继承 / 实现 | `line-arrow` | 1 | 4 | 实现为虚线 `6 3` |
| 依赖 | `line-arrow` | 1 | 2 | 虚线 `6 3` |

类图关系额外写 `data.capsCustomized = true`。

---

## 五、坐标与排版

### 5.1 基本约定

- 单位是 px；`position` 是节点左上角，`size` 是宽高
- 所有坐标为绝对值；父容器只负责分组/移动，不改变子节点坐标基准
- `zIndex` 建议分层：分区 0、组盒 1、普通节点 2–9、连线 10+
- 边不需要 `size`，其包围盒由端点、`vertices`、标签推导

### 5.2 导入不会自动排版

导入只执行升级、反序列化、补标题与 `topicOrder`，**不会**调用自动布局。因此：

- `position` 必须就是期望的最终位置
- `data.layout` 影响方向按钮和后续新增节点时的布局方向，但不会在打开时重排
- 之后在画布上增删子节点，整棵树会按 `data.layout` 重新排版，手算位置会被覆盖

### 5.3 文本尺寸

主题和文本节点**不会按文案自动撑开**，尺寸过小会溢出或挤压换行。按内容留足：

- 中文按 `字号 × 字数` 估算
- 英文/数字按 `字号 × 0.55 × 字符数` 估算
- 再加 2px 余量

节点尺寸建议：根主题高约 44、宽 120–160；子主题高约 34、宽 80–140。

---

## 六、可编辑性（决定模板质量）

模板是给用户改文案、改颜色、改位置的，不是一张合成图。

| 原则 | 要求 |
| --- | --- |
| 文案独立成节点 | 卡片、标注、分栏标题 → 每条文案一个 `text-node` |
| 装饰框不写文案 | 白底卡片、色条、外框 → `attrs.label.text` 为空字符串 |
| 连线绑结构 | 边挂在形状节点上，**不挂** `text-node` |
| 尺寸防溢出 | 每个 `text-node` 显式写 `position` / `size`，且落在父容器内 |
| id 可读 | 用 `c1-bg`、`c1-title`、`in-desc` 这类语义 id，便于后续指代 |

**例外**——文字可以写在 `shape-*` 的 label 上：

- 简单流程图单步（一个矩形 = 一步，整体拖动）
- 形状未旋转、文字与形状一一对应（如胶囊标签）
- 反之，形状带旋转/变形（鱼头三角、斜向骨线）时，文字要单独放 `text-node` 浮在合适位置，**不与任何节点连线**

---

## 七、生成检查清单

- [ ] 顶层是 `{ "cells": [...] }`，JSON 可解析
- [ ] 所有 `id` 唯一且非空
- [ ] 每个节点有 `shape`、`position`、`size`
- [ ] 所有 `shape` 都在已注册清单内
- [ ] 每条边的 `source.cell` / `target.cell` 都能在 `cells` 里找到
- [ ] **没有自由端点边**：所有边的端点都含 `cell`
- [ ] **没有用矩形假造连线**：结构线一律是 `shape: "edge"`
- [ ] 隐形锚点为 1×1 + `fill:none` + `stroke:none` + 无 `label` + `zIndex: 0`
- [ ] 隐形锚点数量 ≤ 10，且每个都服务于「真实节点上没有的落点」
- [ ] 锚点的 `anchor.name` 与对齐方式匹配（left→x，right→x+1，top→y，bottom→y+1）
- [ ] 树边没有 `data.lineType`，有 `data.topicOrder` 与 `targetMarker: null`
- [ ] 普通连接线有合法 `data.lineType`、`attrs.line` 和 `startCap` / `endCap`
- [ ] 表格 `cells` 每行等长，`colWidths` / `rowHeights` 长度匹配，`size` 等于总和
- [ ] 网格类布局所有格子等高，`size.height` 等于行高之和
- [ ] 分区同时有 `data.title` 和 `attrs.label.text`
- [ ] `group` / `section` 的 `children` 与子节点 `parent` 一致，组盒 `zIndex` 低于成员
- [ ] 多行文字用 `label.html`；表格文字已做 HTML 转义
- [ ] 所有字号在 12 / 14 / 16 / 18 / 20 白名单内，正文为 14
- [ ] 字号校验用的是白名单，不是 `fontSize < 12`
- [ ] 调字号后未出现文字溢出、裁切或异常换行
- [ ] 全圆角矩形用 `shape-full-rounded-rect`，不是 `rx = h/2`
- [ ] 六边形朝向正确（需要平顶时未依赖默认朝向）
- [ ] 弧 / 环是填充面（有 `fill` + `strokeWidth: 0`），不是粗描边
- [ ] 环带范围内无任何背景色形状，逐度扫描无空洞
- [ ] 未写 `tools`、`view`、`selection`、`hover`、`collapse` 等 UI 字段

---

## 八、常见问题速查

| 现象 | 原因 | 修复 |
| --- | --- | --- |
| 文字显示「输入文本」 | `attrs.label.text` 没写或层级写错 | 写到 `attrs.label.text`；富文本用 `attrs.label.html` |
| 节点导入后消失 | `shape` 未注册且不以 `shape-` 开头 | 改用已注册名称；拼错 `shape-*` 会退化为圆角矩形 |
| 边整条不存在 | 端点指向不存在的 id，导入时整条丢弃 | 先确保节点存在，再写边 |
| 线悬空 / 穿过图形 | 不规则图形用了包围盒锚点 | 端点改用 `shape-boundary` |
| 思维导图线样式不对 | 树边缺 `connector` 或误写了 `data.lineType` | 树边不写 `lineType` |
| 思维导图线端出现箭头 | 树边没写 `targetMarker: null` | 显式写 `null` |
| 普通连线被当成树结构 | 漏写 `data.lineType` | 补上 |
| 连线整体漂移、箭头指向空白 | 用了自由端点 `{x, y}` | 改绑定端点；需要精确落点时插 1×1 锚点 |
| 拖动节点时连线不跟随 | 结构线其实是细矩形或自由端点 | 改成绑定节点的 `edge` |
| 连线和目标差 1px 没贴住 | 1×1 锚点被两种方向共用，或对齐公式算错 | 一个锚点只服务一个方向 |
| 画面上有莫名小方块 | 锚点写了 `label` 或 `fill` 不为 `none` | 锚点不写 `label`，`fill`/`stroke` 都是 `none` |
| 一部分连线莫名消失 | 连线挂在隐形锚点上，锚点被当空对象清理 | 改绑真实节点；锚点控制在 10 个内 |
| 表格尺寸 / 行高不对 | `size` 与列宽行高不一致，或 `rowDragged` 为 `false` | 对齐 `size`；需要固定行高时写 `rowDragged: true` |
| 表格内容丢失 / 变成空表 | `cells` 为空、非矩形或首行为空 | 保证矩形矩阵且至少一行一列 |
| 网格格子高低不齐、中间空一截 | 各格行数不同导致高度不同 | 统一行数，`Q_H` 由行数反算 |
| 分区标题变成「分区」 | 只写了 `attrs.label.text` | `data.title` 与 `attrs.label.text` 都写 |
| 组移动时子节点不跟随 | 子节点没有 `parent`，或 `children` 与 `parent` 不一致 | 两边都写并保证 id 对应 |
| 颜色不生效 / 看不见 | `fill` 为 `none`，或 `fillOpacity` / `strokeOpacity` 为 0 | 检查 fill 与 opacity |
| 字号看着比别处小一档 | 写了 13px（或 10/11/15/17） | 改成 14 或 12 |
| 胶囊两端不是半圆 | 用了 `shape-rounded-rect` + `rx = h/2` | 改用 `shape-full-rounded-rect` |
| 六边形拼不上、斜向贴住 | 用了默认朝向或间距公式不对 | 自画 6 顶点平顶六边形，间距先向外扩 `g/2` |
| 环 / 弧边缘锯齿、有接缝 | 用粗描边画环 | 改成填充多边形 |
| 圆环断开 | 环带范围内压了背景色形状 | 环内禁用白色形状；箭头做成轮廓自带内凹的实心多边形 |
| 文案整体左偏 | `textAnchor: "middle"` 缺 `refX` | 改 `textAnchor: "start"` + `refX: 0`，`position.x` 即左边缘 |

---

## 延伸阅读

| 文档 | 内容 |
| --- | --- |
| [references/builder-workflow.md](references/builder-workflow.md) | 用脚本批量生成：Builder API、断言校验、几何图元算法 |
| [references/visual-verification.md](references/visual-verification.md) | 照着参考图复刻：像素测量与验收方法 |
| [references/index.md](references/index.md) | 按「图形骨架」选型：14 类图的实现要点 |
| [references/design-system.md](references/design-system.md) | 配色、字号、间距的视觉规范 |
