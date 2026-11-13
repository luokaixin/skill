# 用脚本生成，而不是手写 JSON

图复杂到一定程度后，**手写 JSON 一定会出错**：坐标靠心算、改一个尺寸要连带改几十处、
字号容易飘、自由端点与悬空引用无法自查。

正确做法是**用一个小脚本生成 JSON，再用断言校验**。本文给出可直接复用的构件与写法。

## 0. 为什么值得上一套脚本

| 手写 JSON | 脚本生成 |
| --- | --- |
| 坐标靠心算，改尺寸要连带改几十处 | 尺寸是变量，改一处全图联动 |
| 字号容易写成 13 / 15 | 白名单断言直接拦死 |
| 自由端点、悬空引用无法自查 | 断言检查 |
| 改动后不知道哪些地方受影响 | 改参数 → 重跑 → 断言通过才算完 |
| 无法做像素级验收 | 可渲染成 PNG 后逐像素比对 |

脚本不要求多复杂，一个文件、百来行足够。

## 1. 目录约定

```
project/
├── _lib/
│   └── drawnix.py          # 共享构件（assets/drawnix.py 可直接用）
├── refs/                   # 参考图存档
└── <分类>/
    ├── build.py            # 生成脚本（唯一真相）
    └── out.json            # 产物，由 build.py 生成，不要手改
```

**产物永远由脚本生成。** 手改 JSON 会在下次重跑时被覆盖，而且断言不再反映真实状态。

## 2. build.py 骨架

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图的名称

## 结构          ← 用文字画一遍版式，便于后续维护
## 尺寸依据      ← 有参考图时必写：所有比例的出处
## 实现要点      ← 关键约束，为什么这么写
"""

import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_lib"))
from drawnix import Builder, FS, FS_MIN, FS_SUB, FS_TITLE, INK, MUTED

b = Builder()

X0, TITLE_Y = 140, 44          # 版式原点，全图统一

# ---------- 1. 视觉 token ----------
# ---------- 2. 版式 token（全部写成变量，禁止散落魔数）----------
# ---------- 3. 画图 ----------
# ---------- 4. 保存 + 通用校验 ----------
b.save("out.json")
b.verify("图表名", expect_edges=0, max_anchors=0)

# ---------- 5. 本图专属断言 ----------
by = {c["id"]: c for c in b.cells}
assert ...
```

三段缺一不可：**通用校验**保证不违反契约，**专属断言**保证这张图长得对。
只跑通用校验的图，几何仍然可能错 —— 通用校验不知道「蜂巢应该六边形等距」。

## 3. Builder API

完整实现见 [assets/drawnix.py](../assets/drawnix.py)。

### 3.1 文本

| 方法 | 用途 |
| --- | --- |
| `text(cid, x, y, txt, size=FS, fill=INK, bold=False, width=None)` | 左对齐，`x` 即左边缘 |
| `text_c(cid, cx, y, txt, ...)` | 水平居中，内部按文字宽度反推左边界 |

`text()` 的高度由**宽度反算行数**（`lines = ceil(text_width / width)`）。
传了 `width` 就会自动给多行高度，但**不要传过小的 width**，否则行数算多、高度虚高。

### 3.2 基础图形

| 方法 | 产物 | 说明 |
| --- | --- | --- |
| `rect(cid, x, y, w, h, ...)` | `shape-rect` | 直角矩形 |
| `rounded(cid, x, y, w, h, txt="", rx=8, ...)` | `shape-rounded-rect` | 圆角矩形；`rx=0` 得直角 |
| `pill(cid, x, y, w, h, txt="", ...)` | `shape-full-rounded-rect` | **全圆角矩形** |
| `hexagon(cid, cx, cy, w, h, ...)` | 6 顶点闭合多边形 | **平顶六边形** |
| `circle(cid, cx, cy, d, fill, ...)` | `shape-circle` | 支持 `stroke` / `dashed` / `fill_opacity` |
| `diamond(cid, cx, cy, w, h, ...)` | `shape-diamond` | 判定菱形 |

`pill()` 与 `hexagon()` 的存在就是为了绕开两个形状陷阱，详见 README 3.3。

### 3.3 折线与多边形

| 方法 | 说明 |
| --- | --- |
| `pen(cid, pts, stroke, sw, fill, closed, dash, fill_opacity)` | **绝对坐标**折线/多边形 |

`pen()` 是画任意形状的唯一入口。它会**成对写全** `attrs.penPath.d` 与 `data.points` ——
这两个字段缺任何一个，图形**完全不可见**（不是显示异常，是彻底看不见，且没有任何报错）。

任何自定义轮廓都必须走 `pen()`，不要用多个矩形拼凑。

### 3.4 几何图元

| 方法 | 用途 |
| --- | --- |
| `arc_pts(cx, cy, r, a0, a1, n)` | 圆弧采样点 |
| `arc_arrow(cid, cx, cy, r, start_deg, end_deg, ...)` | 多段开口弧 + 各自箭头（循环图） |
| `ring_arrow(cid, cx, cy, r, sw, tip_deg, ...)` | 完整闭环 + 燕尾箭头（飞轮类） |
| `loose_arrow(cid, cx, cy, size, angle_deg, ...)` | 装饰性孤立三角 |

### 3.5 表格与连线

| 方法 | 说明 |
| --- | --- |
| `table(cid, x, y, rows, col_widths, row_heights, ...)` | `table-node`，`size` 自动等于宽高之和 |
| `anchor(cid, x, y, name)` | 1×1 隐形锚点（数量必须 ≤10） |
| `edge(cid, src, src_anchor, dst, dst_anchor, arrow=True, dashed=False, line_type=None)` | 绑定端点的连线 |

### 3.6 收尾

| 方法 | 说明 |
| --- | --- |
| `save(path)` | 写出 `{ "cells": [...] }` |
| `verify(label, expect_edges, max_anchors, ...)` | 契约级断言 |

## 4. 两个容易写错的图元

### 4.1 全圆角矩形必须用 `pill()`

`shape-full-rounded-rect` 的圆角由**形状类型本身**保证（两端完整半圆）。

**错误写法**：`rounded(...)` + `rx = h/2`。看起来一样，但 `rx` 是普通圆角矩形的参数，
渲染时会被上限裁剪，一旦裁剪就退回普通圆角矩形 —— 两端不再是半圆，
而**从 JSON 上完全看不出问题**（`rx` 的值确实等于 `h/2`）。

**判据**：`shape` 字段必须是 `shape-full-rounded-rect`。

### 4.2 六边形必须用 `hexagon()`

`shape-hexagon` 的朝向（平顶/尖顶）和斜边内缩量由渲染实现决定，无法通过 JSON 控制。
蜂巢拼接必须平顶，所以用 6 顶点 `pen-stroke` 自己画，朝向与比例完全可控。

配套断言：

```python
top_y = min(p["y"] for p in pts)
assert len([p for p in pts if abs(p["y"] - top_y) < 0.01]) == 2, "尖顶六边形"
```

## 5. 几何图元的正确画法

### 5.1 弧 / 环：必须画成「实心填充面」

| 错法 | 症状 |
| --- | --- |
| 一条 `pen-stroke` 粗描边（`strokeWidth` = 环厚） | 每段折线是独立矩形，拐角 `linejoin` 不稳 → **锯齿 + 接缝** |
| `shape-pie` | 只能画实心扇形，挖不出中心空洞，无法单独设描边色 |

**正解**：外弧正向采样 + 内弧反向采样 + `Z` 闭合 = 一整块实心环形面，
`fill` 填色、`strokeWidth: 0`。

```python
outer = [pt(a, r_out) for a in arc_angles]
inner = [pt(a, r_in) for a in reversed(arc_angles)]
poly  = outer + inner          # 首尾自然闭合
```

### 5.2 环上有箭头：环必须完整，且不能有背景色形状压在环上

这是最容易反复出错的一处。判断标准很简单：

> **环带范围内只要出现背景色像素，环在视觉上就是断的。**

三种错法：

| 错法 | 结果 |
| --- | --- |
| 环留缺口、再用箭头去补 | 缺口两侧环端总有一处露白缝 |
| 环完整 + 白色燕尾槽压在环带正中 | 白槽横贯环带 → 环被劈成两截 |
| 环完整 + 白槽够深够宽 | 直接挖穿环带 |

**正解**：箭头是**一个斜跨环带的实心多边形**，与环同色，轮廓本身带内凹（形成燕尾观感），
**全程不用任何白色形状**。

用归一化坐标表示（环厚 = 1，环中线 = 0）：

| 部位 | 径向范围 | 角度范围 |
| --- | --- | --- |
| 环带 | −0.50 … +0.50 | 360° 全覆盖 |
| 箭头轮廓 | −1.30 … +1.50 | 约 −14° … +13° |

自检必须能拦住「环带被挖洞」：

```python
holes = [d for d in range(360) if not band_has_fill(d)]
assert not holes, f"环在 {holes} 度被挖洞"
```

### 5.3 蜂巢：间距要先「向外扩 g/2」再密铺

直接写 `DX = 0.75 × 格宽` 会让**横向缝比纵向窄**，斜向格子贴住而上下留空。

```python
GAP = 16                                    # 六个方向统一白缝
CELL_W = HEX_W + 2 * GAP / math.sqrt(3)     # 扩边后等效格宽
CELL_H = HEX_H + GAP
DX = CELL_W * 0.75                          # 水平相邻中心距
DY = CELL_H                                 # 垂直相邻中心距
```

六个格子中心：`(0, ±DY)` 与 `(±DX, ±DY/2)`。

**不要用角度摆**（每 60° 取一个 `cos/sin`）—— 角度摆法会让斜向格子与中心格的边对不齐。

### 5.4 网格类布局：格子必须等高

`table-node` 高度由自己的 `rowHeights` 之和决定。若各格行数不同（左上 3 条、左下 2 条），
高度就不同，而坐标仍按统一 `Q_H` 推算 → 中间空出一段、上下排下沿不齐、轴标签悬空。

```python
HEAD_H, ROW_H, ROWS = 46, 46, 5
Q_H = HEAD_H + ROW_H * ROWS        # 高度由行数反算，不预设
rows = [[title]] + [[t] for t in items] + [[""] for _ in range(ROWS - len(items))]
```

空行铺成**等高空行**，不要用一条超高填充行代替。

### 5.5 时序图：不要依赖自带生命线的图元

`shape-object-lifeline` / `shape-focus-control` 这类图元自带内部渲染，包围盒与实际可见范围不一致，
坐标不可控，消息线端点无法可靠对齐。

改用基础图形自己拼：

| 元素 | 实现 |
| --- | --- |
| 参与者框 | `shape-rounded-rect`，220×58 |
| 生命线 | `edge`，从框底绑到底部锚点，`strokeDasharray: "5 4"` |
| 激活条 | `shape-rect`，宽 26，浅色填充，**不写 `attrs.label`** |
| 消息线 | `edge` 绑定两个 1×1 锚点，`endCap: 3`（实心）/ `11`（开放箭头，用于返回） |
| 消息文案 | `text-node`，`textAnchor: "start"` + `refX: 0` |

关键：消息端点要落在**激活条外缘**，不是生命线中心（外移半个激活条宽，通常 13px），
否则箭头会被激活条遮住一截。

激活条要按消息区间**合并连续段**，否则会出现「一条长条贯穿全图」或「每两条消息一个碎条」：

```python
spans = {}
for idx, frm, to, *_ in MESSAGES:
    for key in {frm, to}:
        spans.setdefault(key, []).append(msg_y(idx))

for key, ys in spans.items():
    ys = sorted(set(ys))
    cluster = [ys[0]]
    for y in ys[1:]:
        if y - cluster[-1] <= STEP * 2:      # 相邻消息并入同一段
            cluster.append(y)
        else:
            FOCUS.append((key, cluster[0], cluster[-1])); cluster = [y]
    FOCUS.append((key, cluster[0], cluster[-1]))
```

## 6. 断言清单

`verify()` 内置以下检查，任一失败即退出：

| 检查 | 拦住的错误 |
| --- | --- |
| id 唯一 | 重复 id |
| 无自由端点 | `{x, y}` 端点（导入后会漂移） |
| 无悬空引用 | 端点指向不存在的 id |
| 无斜线（可选放宽） | 两端不在同一水平/竖直线 |
| 箭头类型 ⊆ {1, 3} | 用了非常规 `endCap` |
| 节点不重叠 | 排除 `a-*` / `deco-*` / `cont-*` 前缀 |
| 字号白名单 | 9/10/11/13/15/17/19 |
| 连线数匹配 | `expect_edges` 不符 |
| 锚点 ≤ 上限（默认 10） | 空壳节点过多 |

`verify()` 只管契约，不管「长得对不对」。每张图还要写自己的断言：

```python
# 等距 / 等高 / 对齐
assert len({round(t["size"]["height"]) for t in tabs}) == 1
# 中心落在网格上
assert abs(ccx - (CX + ox)) < 0.5
# 元素不溢出容器
assert hx1 < PANEL_X + PANEL_W - 8
# 文字宽不超该高度处的可用内宽
assert w / 2 <= inner_half_width(off) + 0.5
# 环带无空洞
assert not [d for d in range(360) if not band_has_fill(d)]
```

## 7. 渲染预览

`assets/preview.py` 把 JSON 渲染成 PNG，用于目视与像素比对：

```bash
python3 assets/preview.py <json路径> <输出.png>
# 超采样 4 倍再缩回，模拟抗锯齿
SS_SCALE=4 python3 assets/preview.py <json路径> <输出.png>
```

> **预览器的锯齿不代表产物有问题。** 简单渲染器通常不做抗锯齿，粗描边折线必然呈阶梯状。
> 判断「是否有锯齿」要看 JSON 用的是填充面还是粗描边（见 5.1），不要只看 PNG。

## 8. 新图 checklist

- [ ] `build.py` + 生成的 `out.json`
- [ ] docstring 三节齐全：结构、尺寸依据、实现要点
- [ ] 视觉与版式参数全部变量化，无散落魔数
- [ ] `verify()` 通过
- [ ] 本图专属断言 ≥4 条
- [ ] 渲染 PNG 目视一遍
- [ ] 全量重跑所有 `build.py`，确认没有互相影响
