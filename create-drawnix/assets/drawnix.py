#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drawnix 白板 JSON 通用构件

只收录已验证可用的写法，避免每个生成脚本各写一套、各踩各的坑。

## 硬规则

1. 连线必须是 `shape: "edge"`，两端**绑定节点**（`cell` + `anchor`），
   不写自由端点 `{x, y}` —— 自由端点导入后会整体漂移。
2. 不要用 `vertices` 补偿漂移，它同样是自由坐标。
3. 不要用细矩形假造连线：拖动节点不跟随、导出即失效。
4. 箭头用三角箭头 `endCap: 3`。
5. 连线的端点只能取节点四条边的中点，所以一条边要么水平、要么竖直；
   想竖直相连就把节点对齐到同一列。
6. 表格/类框要**等高**，否则同一行的 `left/right` 锚点高度不同，连线会变斜。
7. 文案用 `text-node` + `textAnchor: "start"` + `refX: 0`，`position.x` 即左边缘。
8. 字号 ≥ 12，正文 14。
"""

from unicodedata import east_asian_width

# ---------------- 视觉 token ----------------
INK = "#1F2329"
MUTED = "#646A73"
BORDER = "#BFC3CC"
LINE = "#2F3B4D"

# 字号阶梯：只有 12 / 14 / 16 / 18 / 20（+ 少量更大标题）
# **禁止 9 / 10 / 11 / 13**。正文用 14，辅助信息用 12，不要有中间态。
FS = 14          # 正文默认；最小可用字号就是 12
FS_SM = FS       # 兼容既有调用；语义上等于正文，不再有 13px
FS_MIN = 12      # 唯一允许的辅助字号
FS_SUB = 16      # 卡片标题
FS_TITLE = 20    # 页面 / 分区标题

ALLOWED_SIZES = {12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40, 42, 48}


def text_width(text, size=FS):
    """粗估文字宽度：中日韩算 1 个字号，西文数字算 0.58。"""
    return sum(size * (0.58 if east_asian_width(c) in ("Na", "N") else 1.0)
               for c in text)


class Builder:
    """收集 cells，自动维护 zIndex。"""

    def __init__(self):
        self.cells = []
        self._z = 0

    def nz(self):
        self._z += 1
        return self._z

    # ---------- 文本 ----------
    def text(self, cid, x, y, txt, size=FS, fill=INK, bold=False,
             width=None, angle=None):
        w = width if width is not None else round(text_width(txt, size) + 10, 1)
        # 高度按「宽度能装几个字」反算行数。写死 1 行会让长文案折行后压出边界，
        # 而模板里的说明文字经常 20+ 字，必须按实际行数给高度。
        lines = 1
        if width is not None and width > 0:
            need = text_width(txt, size)
            if need > width:
                lines = int(-(-need // width))      # 向上取整
        lh = round(size * 1.5)
        h = round(lines * lh + (size * 0.1), 1)
        cell = {
            "id": cid,
            "shape": "text-node",
            "position": {"x": round(x, 1), "y": round(y, 1)},
            "size": {"width": w, "height": h},
            "attrs": {"label": {"text": txt, "fill": fill, "fontSize": size,
                                "fontWeight": "bold" if bold else "normal",
                                "lineHeight": lh,
                                "textAnchor": "start", "refX": 0}},
            "data": {"textManualResized": True},
            "zIndex": self.nz(),
        }
        if angle is not None:
            cell["angle"] = angle
        self.cells.append(cell)
        return cell

    # ---------- 形状 ----------
    def rect(self, cid, x, y, w, h, fill="none", stroke="none", sw=0,
             dashed=False, z=None):
        cell = {
            "id": cid,
            "shape": "shape-rect",
            "position": {"x": round(x, 1), "y": round(y, 1)},
            "size": {"width": round(w, 1), "height": round(h, 1)},
            "attrs": {"body": {"fill": fill, "stroke": stroke, "strokeWidth": sw,
                               "strokeDasharray": "6 4" if dashed else "none"}},
            "data": {"manualResized": True},
            "zIndex": self.nz() if z is None else z,
        }
        self.cells.append(cell)
        return cell

    def rounded(self, cid, x, y, w, h, txt="", fill="none", stroke=BORDER,
                sw=1.5, rx=8, fs=FS, text_fill=INK, z=None):
        cell = {
            "id": cid,
            "shape": "shape-rounded-rect",
            "position": {"x": round(x, 1), "y": round(y, 1)},
            "size": {"width": round(w, 1), "height": round(h, 1)},
            "attrs": {
                "body": {"fill": fill, "stroke": stroke, "strokeWidth": sw,
                         "rx": rx, "ry": rx},
                "label": {"text": txt, "fontSize": fs, "fill": text_fill},
            },
            "data": {"manualResized": True},
            "zIndex": self.nz() if z is None else z,
        }
        self.cells.append(cell)
        return cell

    def pill(self, cid, x, y, w, h, txt="", fill="none", stroke=BORDER,
             sw=1.5, fs=FS, text_fill=INK, z=None):
        """全圆角矩形（stadium / 胶囊）：两端是完整半圆，圆角 = 高度的一半。

        **不要**用 `shape-rounded-rect` + `rx = h/2` 来冒充 —— 那是「圆角矩形
        的极限」，渲染端一旦对 rx 做上限裁剪，就退回成普通圆角矩形。
        绘制胶囊必须用 `shape-full-rounded-rect`，它由形状类型本身保证
        两端是半圆，不依赖任何数值参数。
        """
        cell = {
            "id": cid,
            "shape": "shape-full-rounded-rect",
            "position": {"x": round(x, 1), "y": round(y, 1)},
            "size": {"width": round(w, 1), "height": round(h, 1)},
            "attrs": {
                "body": {"fill": fill, "stroke": stroke, "strokeWidth": sw},
                "label": {"text": txt, "fontSize": fs, "fill": text_fill},
            },
            "data": {"manualResized": True},
            "zIndex": self.nz() if z is None else z,
        }
        self.cells.append(cell)
        return cell

    def hexagon(self, cid, cx, cy, w, h, fill="#FFFFFF", stroke=INK, sw=1.5,
                z=None):
        """平顶六边形（**上下平边、左右尖角**），用闭合 `pen-stroke` 显式绘制。

        ## 为什么不用原生 `shape-hexagon`

        `shape-hexagon` 虽然已注册，但朝向（平顶 / 尖顶）和斜边内缩量由渲染端
        决定，我们控制不了。蜂巢图必须**平顶**（参考图实测：顶部平边宽 ≈ 0.5×W，
        左右各一个尖角），一旦渲染端画成尖顶，六格就拼不成蜂窝。
        所以这里直接给出六个顶点，朝向和比例 100% 可控。

        ## 顶点（平顶，顺时针）

            (x0+k, y0)──(x1-k, y0)          ← 上平边，宽 = W − 2k
                      ╲            ╱
                       (x1, cy)                 ← 右尖角
                      ╱            ╲
            (x0+k, y1)──(x1-k, y1)          ← 下平边

        k 取 0.25×W 时上平边正好是 W/2 —— 与参考图实测的 0.52×W 吻合。
        """
        k = w * 0.25
        x0, x1 = cx - w / 2.0, cx + w / 2.0
        y0, y1 = cy - h / 2.0, cy + h / 2.0
        pts = [(x0 + k, y0), (x1 - k, y0), (x1, cy),
               (x1 - k, y1), (x0 + k, y1), (x0, cy)]
        rel = [(round(x - x0, 2), round(y - y0, 2)) for x, y in pts]
        d = "M " + " L ".join(f"{x} {y}" for x, y in rel) + " Z"
        self.cells.append({
            "id": cid,
            "shape": "pen-stroke",
            "position": {"x": round(x0, 1), "y": round(y0, 1)},
            "size": {"width": round(w, 1), "height": round(h, 1)},
            "attrs": {"penPath": {"d": d, "stroke": stroke, "strokeWidth": sw,
                                  "strokeOpacity": 1, "fill": fill,
                                  "strokeLinecap": "butt",
                                  "strokeLinejoin": "miter"}},
            "data": {"isPenStroke": True,
                     "points": [{"x": x, "y": y} for x, y in rel],
                     "strokeWidth": sw},
            "zIndex": self.nz() if z is None else z,
        })
        return self.cells[-1]

    def circle(self, cid, cx, cy, d, fill, txt="", fs=FS, text_fill="#FFFFFF",
               stroke=None, sw=1, dashed=False, fill_opacity=None, z=None):
        body = {"fill": fill, "stroke": stroke or fill, "strokeWidth": sw}
        if dashed:
            body["strokeDasharray"] = "6 4"
        if fill_opacity is not None:
            body["fillOpacity"] = fill_opacity
        cell = {
            "id": cid,
            "shape": "shape-circle",
            "position": {"x": round(cx - d / 2, 1), "y": round(cy - d / 2, 1)},
            "size": {"width": d, "height": d},
            "attrs": {"body": body},
            "data": {"manualResized": True},
            "zIndex": self.nz() if z is None else z,
        }
        if txt:
            cell["attrs"]["label"] = {"text": txt, "fontSize": fs,
                                      "fill": text_fill, "fontWeight": "bold"}
        self.cells.append(cell)
        return cell

    def text_c(self, cid, cx, y, txt, size=FS, fill=INK, bold=False, width=None):
        """水平居中的 text-node：按估算宽度反推左边界。

        视觉居中靠 `position.x = cx - w/2` 实现，不写 `textAnchor: middle`
        （契约里左对齐才是默认可用写法）。
        """
        w = width if width is not None else round(text_width(txt, size) + 8, 1)
        return self.text(cid, cx - w / 2, y, txt, size=size, fill=fill,
                         bold=bold, width=w)

    def diamond(self, cid, cx, cy, w, h, txt="", fill="none", stroke=LINE,
                sw=1.5, fs=FS):
        cell = {
            "id": cid,
            "shape": "shape-diamond",
            "position": {"x": round(cx - w / 2, 1), "y": round(cy - h / 2, 1)},
            "size": {"width": w, "height": h},
            "attrs": {"body": {"fill": fill, "stroke": stroke, "strokeWidth": sw},
                      "label": {"text": txt, "fontSize": fs, "fill": INK}},
            "data": {"manualResized": True},
            "zIndex": self.nz(),
        }
        self.cells.append(cell)
        return cell

    # ---------- 折线 / 多边形（雷达图、环形图、装饰线） ----------
    def pen(self, cid, pts, stroke="#333", sw=2, fill="none", closed=False,
            linecap="round", dash=None, fill_opacity=None, z=None):
        """绝对坐标折线或闭合多边形，统一走 `pen-stroke`。

        **必须同时写 `attrs.penPath.d` 与 `data.points`**，缺一个就完全不可见
        （缺任一个都会导致图形完全不可见，且不会报错）。

        sw 取到接近图形尺寸时，可用「密集采样点 + 粗描边」画环带扇段：
        环形图、循环图的弧就是这么做出来的，不依赖任何弧线语法。
        """
        assert len(pts) >= 2, f"{cid} 至少两个点"
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        rel = [(round(x - x0, 2), round(y - y0, 2)) for x, y in pts]
        d = "M " + " L ".join(f"{x} {y}" for x, y in rel) + (" Z" if closed else "")

        pen = {"d": d, "stroke": stroke, "strokeWidth": sw,
               "strokeOpacity": 1, "fill": fill, "strokeLinecap": linecap,
               "strokeLinejoin": "round"}
        if dash:
            pen["strokeDasharray"] = dash
        if fill_opacity is not None:
            pen["fillOpacity"] = fill_opacity

        self.cells.append({
            "id": cid,
            "shape": "pen-stroke",
            "position": {"x": round(x0, 1), "y": round(y0, 1)},
            "size": {"width": round(max(xs) - x0, 1) or 1,
                     "height": round(max(ys) - y0, 1) or 1},
            "attrs": {"penPath": pen},
            "data": {"isPenStroke": True,
                     "points": [{"x": x, "y": y} for x, y in rel],
                     "strokeWidth": sw},
            "zIndex": self.nz() if z is None else z,
        })
        return self.cells[-1]

    def arc_pts(self, cx, cy, radius, a0, a1, n=24):
        """圆弧采样点（角度制，0° 指向右，90° 指向下）。"""
        import math
        return [(round(cx + radius * math.cos(math.radians(a0 + (a1 - a0) * i / n)), 2),
                 round(cy + radius * math.sin(math.radians(a0 + (a1 - a0) * i / n)), 2))
                for i in range(n + 1)]

    # ---------- 弧形箭头（循环图：多段开口弧 + 各自的箭头） ----------
    def arc_arrow(self, cid, cx, cy, radius, start_deg, end_deg,
                  color="#A8DCA8", sw=30, head=1.0, z=None, paper="#FFFFFF"):
        """一段**开口弧** + 末端燕尾箭头。用于多段拼接的循环图（PDCA 等）。

        与 `ring_arrow` 的区别：
        - `arc_arrow` 画的是若干段开口弧，每段各带一个箭头，段间留缺口 ——
          适合「四阶段首尾相接」的循环图。
        - `ring_arrow` 画的是**一整圈不掉头的环**，只在一处收头 ——
          适合「增长飞轮」那种单一闭环。

        构造：环身（`butt` 平头）→ 大三角 → 纸色挖口三角，顺序不能换。
        """
        import math

        def pt(deg, r):
            a = math.radians(deg)
            return (cx + r * math.cos(a), cy + r * math.sin(a))

        a_end = math.radians(end_deg)
        tv = (-math.sin(a_end), math.cos(a_end))
        E = pt(end_deg, radius)

        big_w = sw * 2.35 * head
        big_h = sw * 2.60 * head
        notch_w = sw * 0.72 * head
        notch_h = sw * 1.15 * head
        over = sw * 0.50

        ang = round(math.degrees(a_end) + 180, 1)

        th = math.radians(ang)
        dirx, diry = math.sin(th), -math.cos(th)

        def tri(part, w, h, base_s, fill):
            bx = E[0] + tv[0] * base_s
            by_ = E[1] + tv[1] * base_s
            ccx = bx + dirx * h / 2
            ccy = by_ + diry * h / 2
            self.cells.append({
                "id": f"{cid}-{part}",
                "shape": "shape-triangle",
                "position": {"x": round(ccx - w / 2, 1),
                             "y": round(ccy - h / 2, 1)},
                "size": {"width": round(w, 1), "height": round(h, 1)},
                "attrs": {"body": {"fill": fill, "stroke": fill, "strokeWidth": 0}},
                "data": {"manualResized": True, "decorative": True},
                "angle": ang,
                "zIndex": self.nz() if z is None else z,
            })

        n = 30
        pts = [pt(start_deg + (end_deg - start_deg) * i / n, radius)
               for i in range(n + 1)]
        pts.append((E[0] + tv[0] * over, E[1] + tv[1] * over))

        x0 = min(p[0] for p in pts)
        y0 = min(p[1] for p in pts)
        rel = [(round(p[0] - x0, 2), round(p[1] - y0, 2)) for p in pts]
        d = "M " + " L ".join(f"{x} {y}" for x, y in rel)

        self.cells.append({
            "id": cid,
            "shape": "pen-stroke",
            "position": {"x": round(x0, 1), "y": round(y0, 1)},
            "size": {"width": round(max(p[0] for p in pts) - x0, 1) or 1,
                     "height": round(max(p[1] for p in pts) - y0, 1) or 1},
            "attrs": {"penPath": {"d": d, "stroke": color, "strokeWidth": sw,
                                  "strokeOpacity": 1, "fill": "none",
                                  "strokeLinecap": "butt"}},
            "data": {"isPenStroke": True,
                     "points": [{"x": x, "y": y} for x, y in rel],
                     "strokeWidth": sw},
            "zIndex": self.nz() if z is None else z,
        })

        tri("head", big_w, big_h, -over, color)
        tri("notch", notch_w, notch_h, 0.0, paper)
        return self.cells[-1]

    # ---------- 圆环箭头（增长飞轮） ----------
    def ring_arrow(self, cid, cx, cy, radius, sw, color="#FFFDCA",
                   tip_deg=190.0, z=None, paper="#FFFFFF"):
        """完整闭环 + 环上燕尾箭头。

        ## 铁律：环带里绝不能出现任何背景色像素

        最常见的实现错误都会导致同一个结果：**环带上被挖出背景色的洞**，
        视觉上环被劈成两截。

        * 环留缺口、再用箭头去补 —— 缺口两侧环端总归露白缝；
        * 环完整、再压一个白色燕尾槽 —— 槽一碰到环带就是在环里打洞。

        所以这里**不使用任何白色形状**。箭头由两个**同色**实心三角叠成：
        大三角是箭头本体，小三角退到它的后方、形成台阶状的尾翼（燕尾）。
        两片同色实心面并与环带相接，union 之后是一个完整连通、颜色贯通的
        图形，环带上一个背景色像素都不会有。

        ## 几何

        1. **环**：完整 360° 实心环形面（外弧正向 + 内弧反向 + 闭合）。
           用填充而不是粗描边 —— 粗描边在渲染器里每段折线是独立矩形，
           拐角 `linejoin` 不稳，环会呈锯齿/碎片状。
        2. **箭头**：底边落在环中线上，底宽 `2.0×环厚`（向内外各凸出
           `0.5×环厚`），尖端沿**顺时针切向**探出 `1.5×环厚`。
        3. **尾翼**：小一号的同色三角，底边沿径向退到箭头底边后方
           `0.55×环厚`，宽度 `1.45×环厚` —— 与箭头底边错开，形成燕尾台阶。

        参数
        ----
        tip_deg  箭头底边方位角（0°=右，90°=下；常用 187°–196°）
        """
        import math

        R, half = float(radius), float(sw) / 2.0
        r_out, r_in = R + half, R - half

        def pt(deg, r):
            a = math.radians(deg)
            return (cx + r * math.cos(a), cy + r * math.sin(a))

        # ---- 1. 环：完整 360° 实心环形面 ----
        n = 240
        outer = [pt(360.0 * i / n, r_out) for i in range(n + 1)]
        inner = [pt(360.0 * (n - i) / n, r_in) for i in range(n + 1)]
        poly = outer + inner
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, y0 = min(xs), min(ys)
        rel = [(round(x - x0, 2), round(y - y0, 2)) for x, y in poly]
        d = "M " + " L ".join(f"{x} {y}" for x, y in rel) + " Z"
        self._add_fill_poly(cid, x0, y0, max(xs), max(ys), rel, d, color, z)

        # ---- 2. 箭头：按极坐标轮廓给定的单个填充多边形 ----
        #
        # 0.5° 精度扫描得到的箭头轮廓（相对箭头方位角，径向单位 = 环厚，
        # 0 = 环中线）。环带占 −0.50…+0.50，箭头斜跨环带：
        #
        #   外缘: −13.5°→−1.24 一路张开到 −0.5°→+1.50（尖端），再收到 +12.5°→+0.24
        #   内缘: −13.5°→−1.28 沿环带内侧走到 −0.36（+12.5°）
        #
        # 也就是「一个斜跨环带的大三角，尾部贴着环带内缘拖出一段」。
        # 用多边形直接给出轮廓，而不是「三角形 + 白色挖槽」——
        # 白色挖槽只要碰到环带，环就会断开。
        #
        # 下表的 (角度偏移, 径向偏移) 全部来自参考图实测。
        OUTLINE = [
            # 外缘：从尾角张开到尖端
            (-13.5, -1.24), (-12.0, -1.04), (-10.0, -0.85), (-8.0, -0.56),
            (-6.0, 0.10), (-4.0, 0.55), (-3.0, 0.62), (-2.0, 0.92),
            (-1.0, 1.31), (-0.5, 1.50), (0.0, 1.46), (0.5, 1.40),
            (1.0, 1.32), (2.0, 1.19), (3.0, 1.09), (4.5, 0.91),
            (6.0, 0.76), (7.5, 0.62), (9.0, 0.49), (10.5, 0.37),
            (12.0, 0.24),
            # 前角，折回内缘
            (12.5, -0.36),
            # 内缘：一路退回尾角
            (10.0, -0.49), (8.0, -0.59), (6.0, -0.69), (4.0, -0.78),
            (2.0, -0.86), (0.0, -0.95), (-2.0, -1.00), (-4.0, -1.06),
            (-6.0, -1.12), (-8.0, -1.17), (-10.0, -1.22), (-13.5, -1.28),
        ]
        pts = []
        for d_off, r_off in OUTLINE:
            rad = math.radians(tip_deg + d_off)
            rr = R + r_off * sw
            pts.append((cx + rr * math.cos(rad), cy + rr * math.sin(rad)))

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        rel = [(round(x - x0, 2), round(y - y0, 2)) for x, y in pts]
        d = "M " + " L ".join(f"{x} {y}" for x, y in rel) + " Z"
        self._add_fill_poly(f"{cid}-head", x0, y0, max(xs), max(ys),
                            rel, d, color, z)

        return {
            "ring": cid,
            "tip_deg": tip_deg % 360,
            "head_width": max(xs) - x0,
            "head_len": max(ys) - y0,
            "head_pts": pts,
            "outline": OUTLINE,
            "head_r_max": max(math.hypot(x - cx, y - cy) for x, y in pts),
            "head_r_min": min(math.hypot(x - cx, y - cy) for x, y in pts),
            "base_offset": 0.26 * sw,         # 底边中点比环中线外偏
            "r_out": r_out,
            "r_in": r_in,
        }

    def _add_fill_poly(self, cid, x0, y0, x1, y1, rel, d, color, z=None):
        """把一组顶点写成**实心填充**的 `pen-stroke`（无描边）。

        必须同时写 `attrs.penPath.d` 与 `data.points`，缺一个完全不可见。
        """
        self.cells.append({
            "id": cid,
            "shape": "pen-stroke",
            "position": {"x": round(x0, 1), "y": round(y0, 1)},
            "size": {"width": round(x1 - x0, 1) or 1,
                     "height": round(y1 - y0, 1) or 1},
            "attrs": {"penPath": {"d": d, "stroke": "none", "strokeWidth": 0,
                                  "strokeOpacity": 0, "fill": color,
                                  "strokeLinecap": "butt",
                                  "strokeLinejoin": "miter"}},
            "data": {"isPenStroke": True,
                     "points": [{"x": x, "y": y} for x, y in rel],
                     "strokeWidth": 0},
            "zIndex": self.nz() if z is None else z,
        })
        return self.cells[-1]

    def loose_arrow(self, cid, cx, cy, size, angle_deg, color="#FFFDCA"):
        """环外的装饰性三角，与环体完全脱开。

        参考图实测：最近角距圆心为环外径的 1.24 / 1.43 倍。
        """
        w = h = size
        self.cells.append({
            "id": cid,
            "shape": "shape-triangle",
            "position": {"x": round(cx - w / 2, 1), "y": round(cy - h / 2, 1)},
            "size": {"width": round(w, 1), "height": round(h, 1)},
            "attrs": {"body": {"fill": color, "stroke": color, "strokeWidth": 0}},
            "data": {"manualResized": True, "decorative": True},
            "angle": angle_deg,
            "zIndex": self.nz(),
        })
        return self.cells[-1]

    # ---------- 表格 ----------
    def table(self, cid, x, y, rows, col_widths, row_heights,
              bg="#FFFFFF", border=BORDER, font_size=FS, text_color=INK,
              cell_bg=None, cell_style=None, merges=None, extra_data=None,
              h_align="left", v_align="middle", z=None):
        assert all(len(r) == len(col_widths) for r in rows), f"{cid} 矩阵非矩形"
        data = {
            "cells": rows,
            "colWidths": col_widths,
            "rowHeights": row_heights,
            "rowDragged": [True] * len(rows),
            "merges": merges or [],
            "tableStyle": {
                "bg": bg,
                "borderColor": border,
                "textColor": text_color,
                "fontSize": font_size,
                "hAlign": h_align,
                "vAlign": v_align,
            },
        }
        if cell_bg:
            data["tableStyle"]["cellBackgrounds"] = cell_bg
        if cell_style:
            data["tableStyle"]["cellStyles"] = cell_style
        if extra_data:
            data.update(extra_data)
        cell = {
            "id": cid,
            "shape": "table-node",
            "position": {"x": round(x, 1), "y": round(y, 1)},
            "size": {"width": sum(col_widths), "height": sum(row_heights)},
            "data": data,
            "zIndex": self.nz() if z is None else z,
        }
        self.cells.append(cell)
        return cell

    # ---------- 连线 ----------
    def anchor(self, cid, x, y, name):
        """1×1 隐形锚点。name 决定对齐方式，保证端点精确。

        left → position.x = x        右边缘也在 x（1 宽）
        right → position.x = x - 1
        top → position.y = y
        bottom → position.y = y - 1
        """
        px, py = x - 0.5, y - 0.5
        if name == "right":
            px = x - 1
        elif name == "left":
            px = x
        elif name == "top":
            py = y
        elif name == "bottom":
            py = y - 1
        cell = {
            "id": cid,
            "shape": "shape-rect",
            "position": {"x": round(px, 2), "y": round(py, 2)},
            "size": {"width": 1, "height": 1},
            "attrs": {"body": {"fill": "none", "stroke": "none", "strokeWidth": 0}},
            "data": {"manualResized": True},
            "zIndex": 0,
        }
        self.cells.append(cell)
        return cell

    @staticmethod
    def _bind(cid, name):
        return {"cell": cid,
                "anchor": {"name": name, "args": {"rotate": True}},
                "connectionPoint": {"name": "anchor"}}

    def edge(self, cid, src, src_anchor, dst, dst_anchor,
             arrow=True, dashed=False, color=LINE, sw=1.5,
             line_type=None, router=None):
        """绑定端点的连接线。arrow=True 用三角箭头 endCap=3。

        line_type="polyline" 时用正交折线（arrow-polyline），
        适合两端不在同一水平/竖直线上、又不想手算拐点的场景；
        端点仍然绑定节点，不需要 1×1 隐形锚点。
        """
        lt = line_type or ("line-arrow" if arrow else "line")
        if lt == "polyline":
            connector = {"name": "arrow-polyline", "args": {"radius": 8}}
        elif lt == "curve":
            connector = {"name": "arrow-curve"}
        else:
            connector = {"name": "arrow-line"}

        cell = {
            "id": cid,
            "shape": "edge",
            "source": self._bind(src, src_anchor),
            "target": self._bind(dst, dst_anchor),
            "connector": connector,
            "attrs": {"line": {"stroke": color, "strokeWidth": sw,
                               "strokeDasharray": "6 3" if dashed else "none",
                               "targetMarker": None}},
            "data": {"lineType": lt, "startCap": 1, "endCap": 3 if arrow else 1},
            "zIndex": self.nz(),
        }
        if router:
            cell["router"] = router
        self.cells.append(cell)
        return cell

    # ---------- 输出 ----------
    def save(self, path):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"cells": self.cells}, f, ensure_ascii=False, indent=2)
            f.write("\n")

    # ---------- 通用自检 ----------
    def verify(self, label="", expect_edges=None, allow_free_edges=False,
               allow_skew=False, max_anchors=10):
        """通用断言。max_anchors 为隐形锚点数量上限。

        时序图这类「落点不存在于任何节点上」的图，锚点是设计必需，
        调用方显式放宽 max_anchors 并说明理由。
        """
        by = {c["id"]: c for c in self.cells}
        ids = [c["id"] for c in self.cells]
        assert len(ids) == len(set(ids)), "id 重复"

        edges = [c for c in self.cells if c["shape"] == "edge"]
        free = [(e["id"], s) for e in edges for s in ("source", "target")
                if "cell" not in e[s]]
        dangling = [(e["id"], s) for e in edges for s in ("source", "target")
                    if e[s].get("cell") not in by]
        assert not free or allow_free_edges, f"存在自由端点: {free}"
        assert not dangling, f"悬空引用: {dangling}"

        skew = []
        for e in edges:
            s, t = self._resolve(by, e["source"]), self._resolve(by, e["target"])
            if abs(s[0] - t[0]) > 0.01 and abs(s[1] - t[1]) > 0.01:
                skew.append((e["id"], round(s[0] - t[0], 1), round(s[1] - t[1], 1)))
        assert not skew or allow_skew, f"斜线: {skew}"

        caps = {e["data"].get("endCap") for e in edges}
        assert caps <= {1, 3}, f"箭头类型应为 1 或 3，实际 {caps}"

        # 节点重叠检测。以下是有意叠放、不该判为碰撞的：
        #   a-*     1×1 隐联锚点
        #   deco-*  装饰件（图标、进度条、复选框等）
        #   cont-*  容器底板（面板/泳道/分区），子元素本就落在其中
        deco = ("a-", "deco-", "cont-")
        shapes = [c for c in self.cells
                  if c["shape"] in ("shape-rect", "shape-rounded-rect", "shape-circle",
                                    "shape-diamond", "table-node")
                  and not c["id"].startswith(deco)
                  and c["size"]["width"] > 2
                  and not c.get("data", {}).get("decorative")]
        coll = []
        for i in range(len(shapes)):
            for j in range(i + 1, len(shapes)):
                if self._overlap(self._box(shapes[i]), self._box(shapes[j])):
                    coll.append((shapes[i]["id"], shapes[j]["id"]))
        assert not coll, f"节点重叠: {coll[:5]}"

        # 字号：白名单校验，不是「小于 12 才报错」——9/10/11/13 都要拦住
        bad_sizes = self._bad_font_sizes()
        assert not bad_sizes, (
            f"字号不在允许阶梯内（只许 12/14/16/18/20 及更大标题）：{bad_sizes[:8]}；"
            f"正文用 14，辅助信息用 12")

        if expect_edges is not None:
            assert len(edges) == expect_edges, f"连线数 {len(edges)} != {expect_edges}"

        # 隐形锚点限量：空壳节点过多，导入链路里容易被当空对象清理，
        # 挂在上面的边会被整条丢弃，表现为"连线凭空消失"。
        anchors = [c["id"] for c in self.cells
                   if c.get("size", {}).get("width") == 1
                   and c.get("size", {}).get("height") == 1
                   and (c.get("attrs", {}).get("body") or {}).get("fill") == "none"]
        assert len(anchors) <= max_anchors, (
            f"隐形锚点 {len(anchors)} 个，超过上限 {max_anchors}：{anchors[:12]}；"
            f"改用真实节点端点，或调整布局让两端自然对齐")

        print(f"[{label}] cells={len(self.cells)} edges={len(edges)} "
              f"anchors={len(anchors)} "
              f"endCap={sorted(caps) if caps else '无'} 校验通过")
        return True

    @staticmethod
    def _box(c):
        p, s = c["position"], c["size"]
        return (p["x"], p["y"], p["x"] + s["width"], p["y"] + s["height"])

    def _bad_font_sizes(self):
        """扫描所有字号来源：label、边标签、表格表头与单元格样式。"""
        bad = []

        def chk(cid, where, size):
            if size is None:
                return
            if size not in ALLOWED_SIZES:
                bad.append((cid, where, size))

        for c in self.cells:
            lab = (c.get("attrs") or {}).get("label") or {}
            chk(c["id"], "label", lab.get("fontSize"))
            for i, el in enumerate(c.get("labels") or []):
                chk(c["id"], f"labels[{i}]",
                    ((el.get("attrs") or {}).get("label") or {}).get("fontSize"))
            ts = (c.get("data") or {}).get("tableStyle") or {}
            chk(c["id"], "tableStyle", ts.get("fontSize"))
            for ri, row in enumerate(ts.get("cellStyles") or []):
                if not isinstance(row, list):
                    continue
                for ci, st in enumerate(row):
                    if isinstance(st, dict):
                        chk(c["id"], f"cellStyles[{ri}][{ci}]", st.get("fontSize"))
        return bad

    @staticmethod
    def _overlap(a, b):
        return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

    @staticmethod
    def _resolve(by, t):
        x0, y0, x1, y1 = Builder._box(by[t["cell"]])
        return {"left": (x0, (y0 + y1) / 2), "right": (x1, (y0 + y1) / 2),
                "top": ((x0 + x1) / 2, y0), "bottom": ((x0 + x1) / 2, y1)}[t["anchor"]["name"]]
