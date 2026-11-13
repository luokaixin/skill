# 照着参考图复刻：测量与验收

有参考图（截图、导出图、别人的画板）时，**不能靠肉眼判断像不像**。
视觉判断能发现「整体歪了」，但发现不了「环带被挖了个 3px 的洞」这类致命细节。

正确做法是**先测量再动手**，并把量出来的比例写进断言。本文给出可直接运行的测量方法。

## 0. 四条原则

1. **先测量，再动手。** 拿到参考图第一件事：量尺寸、量颜色、量间距，写进脚本的 docstring。
2. **归一化后再比。** 用「环厚 = 1」「格宽 = 1」这类相对单位。绝对像素不可跨分辨率比较。
3. **判据写进断言。** 量出来的比例要落到 `assert`，否则下次改代码就丢了。
4. **目视只做最后一道。** 它只能确认整体观感，不能用来验收几何。

## 1. 读取基础信息

```python
from PIL import Image
from collections import Counter

im = Image.open(path).convert("RGB")
W, H = im.size
print("尺寸", W, H)
print("主要颜色", Counter(im.getdata()).most_common(8))
```

颜色统计直接给出填充色、描边色、背景色。**不要凭感觉猜色值。**

## 2. 找图形边界

### 2.1 按颜色找连通域

```python
from collections import deque

def components(mask_fn, W, H, px, min_area=200):
    """mask_fn(rgb) -> bool；返回 [(面积, x0, y0, x1, y1)]，按面积降序。"""
    seen = bytearray(W * H)
    out = []
    for y in range(H):
        for x in range(W):
            i = y * W + x
            if seen[i] or not mask_fn(px[x, y]):
                continue
            q = deque([(x, y)]); seen[i] = 1
            n = 0; x0 = y0 = 10**9; x1 = y1 = -1
            while q:
                cx, cy = q.popleft(); n += 1
                x0 = min(x0, cx); x1 = max(x1, cx)
                y0 = min(y0, cy); y1 = max(y1, cy)
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H \
                       and not seen[ny*W+nx] and mask_fn(px[nx, ny]):
                        seen[ny*W+nx] = 1; q.append((nx, ny))
            if n >= min_area:
                out.append((n, x0, y0, x1, y1))
    return sorted(out, reverse=True)
```

**连通域数量本身就是判据。** 例如「一个闭环 + 两个脱离的装饰件」应当是 3 个连通块：
少了说明有元素粘在一起，多了说明主体断了。

### 2.2 按描边找精确边界

填充色连通域会因抗锯齿偏小 1–2px。要精确尺寸就扫描描边（暗像素）：

```python
def dark(rgb, t=160):
    return max(rgb) < t

def v_lines(px, W, ys):
    """在若干行上找暗像素，合并连续段，得到竖直边界的 x。"""
    xs = set()
    for y in ys:
        for x in range(W):
            if dark(px[x, y]):
                xs.add(x)
    xs = sorted(xs); segs = []
    if xs:
        s = pv = xs[0]
        for x in xs[1:]:
            if x - pv > 3:
                segs.append((s, pv)); s = x
            pv = x
        segs.append((s, pv))
    return segs
```

## 3. 极坐标扫描（环形 / 放射状图形专用）

圆形、环形、蜂巢、雷达图的核心判据都在极坐标上。

### 3.1 拟合圆心

先用包围盒中心粗估，再用「环带厚度方差最小」精修：

```python
best = None
for CX in range(cx0 - 40, cx0 + 41):
    for CY in range(cy0 - 40, cy0 + 41):
        ths = []
        for d in test_degs:                  # 避开箭头区域的角度
            hits = [r for r in radii if is_fill(sample(CX, CY, d, r))]
            if hits:
                ths.append(max(hits) - min(hits))
        if len(ths) < len(test_degs) - 2:
            continue
        var = sum((t - sum(ths)/len(ths))**2 for t in ths) / len(ths)
        if best is None or var < best[0]:
            best = (var, CX, CY)
```

环带厚度方差最小的点就是圆心。**不要用包围盒中心代替** —— 不对称凸出（如箭头）会让包围盒偏心。

### 3.2 逐度剖面（发现缺口与挖洞）

```python
import math

def radial_profile(px, W, H, CX, CY, r_lo, r_hi, is_fill):
    """返回 {角度: 该角度上所有填充段 [(r0, r1), ...]}。"""
    prof = {}
    for deg in range(0, 360):
        a = math.radians(deg)
        segs, cur = [], []
        for r in range(r_lo, r_hi):
            x = int(round(CX + r * math.cos(a)))
            y = int(round(CY + r * math.sin(a)))
            ok = 0 <= x < W and 0 <= y < H and is_fill(px[x, y])
            if ok:
                cur.append(r)
            else:
                if cur:
                    segs.append((cur[0], cur[-1])); cur = []
        if cur:
            segs.append((cur[0], cur[-1]))
        prof[deg] = segs
    return prof
```

**判据：环必须每度都有填充。** 任何一度缺失就是断开：

```python
holes = [d for d, segs in prof.items() if not segs]
assert not holes, f"环在 {holes} 度断开"
```

### 3.3 归一化（跨分辨率比较）

```python
R_mid = (r_in + r_out) / 2
sw    = r_out - r_in
norm  = (r - R_mid) / sw        # 环中线 = 0，环厚 = 1
```

归一化后，参考图与产物可以放在同一张表里逐度对比：

| 角度 | 参考图径向段 | 产物径向段 | 偏差 |
| --- | --- | --- | --- |
| 0° | −0.95 … +1.51 | −0.94 … +1.48 | ≤0.03 |
| −13° | −1.28 … −1.22 | −1.25 … −1.17 | ≤0.05 |

**偏差判据建议取 ±0.05 环厚**（约 ±2.5px @ 环厚 50px）。

## 4. 整体相似度（IoU）

对齐后做像素交并比，快速判断版式对不对：

```python
def iou(mask_a, mask_b):
    inter = sum(1 for a, b in zip(mask_a, mask_b) if a and b)
    union = sum(1 for a, b in zip(mask_a, mask_b) if a or b)
    return inter / union
```

对齐方法：按主图形半径缩放，再把两个圆心平移到同一点。

| IoU | 含义 |
| --- | --- |
| > 0.90 | 版式基本一致 |
| 0.80 – 0.90 | 主体对，装饰件位置或尺寸有偏差 |
| < 0.75 | 结构不同，需要重新测量 |

## 5. 逐度 ASCII 图（定位细节缺陷最快）

数值表看不出「形状长什么样」，ASCII 图可以：

```python
print("      " + "".join(str((r // 100) % 10) for r in range(r_lo, r_hi, 4)))
for deg in range(168, 216):
    a = math.radians(deg)
    row = "".join("#" if is_fill(sample(CX, CY, a, r)) else "."
                  for r in range(r_lo, r_hi, 4))
    print(f"{deg:4d}  {row}")
```

一屏内就能看出：形状从哪个角度开始张开、哪里收窄、凹口在什么半径位置。
**数值对得上但形状不对时，ASCII 图能立刻暴露问题。**

## 6. 验收流程

```
1. 测量参考图     颜色统计 → 连通域 → 描边扫描 → 圆心拟合
2. 写进 docstring 归一化比例表（所有魔数的出处）
3. 生成产物       比例全部来自那张表
4. 渲染产物       assets/preview.py
5. 同尺度对比     按主图形半径缩放 + 圆心对齐
6. 三项测量       连通域数 / 逐度剖面 / IoU
7. 目视确认       最后一道，只看整体
```

第 6 步全部通过才算完成。任一项不过就回第 3 步。

## 7. 常见误判

| 误判 | 真相 |
| --- | --- |
| 预览图锯齿严重 → 产物有锯齿 | 简单渲染器不做抗锯齿。要看 JSON 是不是填充面 |
| 数值对上了 → 形状一定对 | 数值只校验采样点，形状可能整体偏移。要配 ASCII 图 |
| 包围盒中心 = 圆心 | 有不对称凸出时会偏心，必须拟合 |
| 连通域数量对 → 结构对 | 还要看面积分配是否合理 |
| 目视「看起来连上了」 | 可能有 1–3px 白缝，要逐度扫描 |
| 低分辨率参考图 → 按比例放大即可 | 抗锯齿会改变实测像素，要取归一化比例再放大 |

## 8. 判据模板（直接抄进脚本）

```python
# ============ 对齐参考图实测 ============
# 1) 主比例（参考图实测：环厚 / 中线半径 = 0.264）
ratio = SW / R
assert abs(ratio - 0.264) < 0.03, f"厚度/半径 {ratio:.3f}，参考 0.264"

# 2) 环必须每度有填充（无挖洞）
holes = [d for d in range(360) if not band_has_fill(d)]
assert not holes, f"环在 {holes} 度断开"

# 3) 连通块数必须等于参考图
assert len(components) == 3, f"连通块 {len(components)} 个，参考图 3 个"

# 4) 关键元素位置（归一化）
assert abs(head_r_max / R - 2.52) < 0.10        # 箭头尖端伸出环外的倍数
assert abs(loose_gap / r_out - 1.43) < 0.08     # 装饰件最近角距圆心 / 环外径
```
