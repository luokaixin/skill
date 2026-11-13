import json, math, re
from PIL import Image, ImageDraw, ImageFont

FP = '/System/Library/Fonts/Hiragino Sans GB.ttc'
import os as _os
_S = int(_os.environ.get('SS_SCALE', '1'))


def font(sz, bold=False):
    return ImageFont.truetype(FP, int(sz * _S), index=2 if bold else 0)


def C(v, d=None):
    return d if v in (None, 'none', 'transparent') else v


def render(path, out, pad=50, bg='#F7F8FA'):
    d = json.load(open(path))
    cells = d['cells']
    shaped = [c for c in cells if 'position' in c]
    W = int(max(c['position']['x'] + c['size']['width'] for c in shaped)) + pad
    H = int(max(c['position']['y'] + c['size']['height'] for c in shaped)) + pad
    import os
    S = int(os.environ.get('SS_SCALE', '1'))
    im = Image.new('RGB', (W * S, H * S), bg)
    dr = ImageDraw.Draw(im, 'RGBA')
    by = {c['id']: c for c in cells}

    def box(c):
        p, s = c['position'], c['size']
        return (p['x'] * S, p['y'] * S,
                (p['x'] + s['width']) * S, (p['y'] + s['height']) * S)

    def rot_pts(pts, cx, cy, deg):
        a = math.radians(deg)
        return [((cx + x * math.cos(a) - y * math.sin(a)) * S,
                 (cy + x * math.sin(a) + y * math.cos(a)) * S) for x, y in pts]

    for c in sorted(cells, key=lambda c: c.get('zIndex', 0)):
        sh = c['shape']
        if sh == 'table-node':
            a = box(c); dd = c['data']; st = dd['tableStyle']
            dr.rectangle([a[0], a[1], a[2], a[3]], fill=C(st.get('bg'), 'white'),
                         outline=C(st.get('borderColor'), '#DDE1E6'), width=1)
            y = a[1]
            cbs = st.get('cellBackgrounds') or []
            css = st.get('cellStyles') or []
            for i, row in enumerate(dd['cells']):
                h = dd['rowHeights'][i]
                rowst = css[i] if i < len(css) else []
                x = a[0]
                for j, val in enumerate(row):
                    cw = dd['colWidths'][j]
                    b = C(cbs[i][j]) if i < len(cbs) and j < len(cbs[i]) else None
                    if b:
                        dr.rectangle([x + 1, y + 1, x + cw - 1, y + h - 1], fill=b)
                    s2 = rowst[j] if rowst and j < len(rowst) and rowst[j] else {}
                    if val not in (None, ''):
                        fsz = s2.get('fontSize', st['fontSize'])
                        f = font(fsz, s2.get('bold', False))
                        ha = s2.get('hAlign', st.get('hAlign', 'left'))
                        sval = str(val)
                        tw = dr.textlength(sval, font=f)
                        tx = x + cw / 2 - tw / 2 if ha == 'center' else x + 10
                        ty = y + h / 2 - fsz * 0.62
                        dr.text((tx, ty), sval, font=f,
                                fill=s2.get('textColor', st.get('textColor', '#1F2329')))
                    x += cw
                y += h
            y = a[1] + dd['rowHeights'][0]
            for i in range(1, len(dd['rowHeights'])):
                dr.line([(a[0], y), (a[2], y)], fill=C(st.get('borderColor'), '#DDE1E6'), width=1)
                y += dd['rowHeights'][i]

        elif sh == 'pen-stroke':
            a = box(c); pen = (c.get('attrs') or {}).get('penPath') or {}
            dd = pen.get('d')
            if not dd:
                continue
            nums = [float(x) * S for x in re.findall(r'-?\d+(?:\.\d+)?', dd)]
            pts = [(a[0] + nums[i], a[1] + nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
            if len(pts) < 2:
                continue
            fill = C(pen.get('fill'))
            stroke = C(pen.get('stroke'))
            sw = max(1, int(float(pen.get('strokeWidth', 2)) * S))
            if dd.rstrip().endswith('Z') and fill:
                dr.polygon(pts, fill=fill, outline=stroke)
            else:
                if fill and fill != 'none':
                    dr.polygon(pts, fill=fill)
                if stroke and stroke != 'none':
                    dr.line(pts, fill=stroke, width=sw, joint='curve')

        elif sh in ('shape-rect', 'shape-rounded-rect', 'shape-full-rounded-rect',
                    'shape-circle', 'shape-triangle', 'shape-trapezoid', 'shape-pie',
                    'shape-parallelogram', 'shape-hexagon', 'shape-diamond'):
            if c['id'].startswith('a-'):
                continue
            a = box(c); bd = c['attrs'].get('body', {}) or {}
            fill = C(bd.get('fill')); stroke = C(bd.get('stroke'))
            sw = max(1, int(float(bd.get('strokeWidth', 0) or 1) * S))
            W0, H0 = a[2] - a[0], a[3] - a[1]

            if sh == 'shape-rect':
                if fill or stroke:
                    dr.rectangle([a[0], a[1], a[2], a[3]], fill=fill, outline=stroke, width=sw)
            elif sh in ('shape-rounded-rect', 'shape-full-rounded-rect'):
                rx = bd.get('rx')
                if rx is None:
                    rx = min(W0, H0) / 2 if sh == 'shape-full-rounded-rect' else 8
                if fill or stroke:
                    dr.rounded_rectangle([a[0], a[1], a[2], a[3]], radius=rx,
                                         fill=fill, outline=stroke, width=sw)
            elif sh == 'shape-circle':
                if fill or stroke:
                    dr.ellipse([a[0], a[1], a[2], a[3]], fill=fill, outline=stroke, width=sw)
            elif sh == 'shape-diamond':
                m = [(a[0] + W0 / 2, a[1]), (a[2], a[1] + H0 / 2),
                     (a[0] + W0 / 2, a[3]), (a[0], a[1] + H0 / 2)]
                dr.polygon(m, fill=fill, outline=stroke)
            elif sh == 'shape-parallelogram':
                k = W0 * 0.16
                m = [(a[0] + k, a[1]), (a[2], a[1]), (a[2] - k, a[3]), (a[0], a[3])]
                dr.polygon(m, fill=fill, outline=stroke)
            elif sh == 'shape-hexagon':
                k = W0 * 0.22
                m = [(a[0] + k, a[1]), (a[2] - k, a[1]), (a[2], a[1] + H0 / 2),
                     (a[2] - k, a[3]), (a[0] + k, a[3]), (a[0], a[1] + H0 / 2)]
                dr.polygon(m, fill=fill, outline=stroke)
            elif sh == 'shape-trapezoid':
                # 上边内缩 20%，下边满宽
                ins = W0 * 0.10
                m = [(a[0] + ins, a[1]), (a[2] - ins, a[1]), (a[2], a[3]), (a[0], a[3])]
                dr.polygon(m, fill=fill, outline=stroke)
            elif sh == 'shape-pie':
                st = bd.get('startAngle', 0) - 90
                en = st + bd.get('sweepAngle', 120)
                dr.pieslice([a[0], a[1], a[2], a[3]], st, en, fill=fill, outline=stroke, width=sw)
            elif sh == 'shape-triangle':
                ang = c.get('angle', 0)
                cx0, cy0 = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
                hw, hh = W0 / 2, H0 / 2
                # 尖端朝上（-y），按实际宽高建三角再旋转
                tri = [(0, -hh), (-hw, hh), (hw, hh)]
                dr.polygon(rot_pts(tri, cx0, cy0, ang), fill=fill, outline=stroke)

    def anch(t):
        n = t['anchor']['name']; a = box(by[t['cell']])
        return {'left': (a[0], (a[1] + a[3]) / 2), 'right': (a[2], (a[1] + a[3]) / 2),
                'top': ((a[0] + a[2]) / 2, a[1]), 'bottom': ((a[0] + a[2]) / 2, a[3])}[n]

    for c in cells:
        if c['shape'] != 'edge':
            continue
        p1, p2 = anch(c['source']), anch(c['target'])
        ln = c['attrs']['line']
        st = ln.get('stroke', '#2F3B4D')
        dash = ln.get('strokeDasharray', 'none')
        if dash and dash != 'none':
            n = 26
            for i in range(0, n, 2):
                q1 = (p1[0] + (p2[0] - p1[0]) * i / n, p1[1] + (p2[1] - p1[1]) * i / n)
                q2 = (p1[0] + (p2[0] - p1[0]) * (i + 1) / n, p1[1] + (p2[1] - p1[1]) * (i + 1) / n)
                dr.line([q1, q2], fill=st, width=max(1, int(ln.get('strokeWidth', 1.5))))
        else:
            dr.line([p1, p2], fill=st, width=max(1, int(ln.get('strokeWidth', 1.5))))
        if c['data'].get('endCap') == 3:
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0]); L = 12; w = 5.5
            dr.polygon([p2,
                        (p2[0] - L * math.cos(ang - w), p2[1] - L * math.sin(ang - w)),
                        (p2[0] - L * math.cos(ang + w), p2[1] - L * math.sin(ang + w))], fill=st)

    for c in cells:
        if c['shape'] in ('shape-rounded-rect', 'shape-circle', 'shape-full-rounded-rect',
                          'shape-rect', 'shape-trapezoid', 'shape-hexagon'):
            lab = c['attrs'].get('label') or {}
            if lab.get('text'):
                a = box(c); f = font(lab['fontSize'], lab.get('fontWeight') == 'bold')
                tw = dr.textlength(lab['text'], font=f)
                dr.text(((a[0] + a[2]) / 2 - tw / 2, (a[1] + a[3]) / 2 - lab['fontSize'] * 0.62),
                        lab['text'], font=f, fill=lab.get('fill', '#1F2329'))

    for c in cells:
        if c['shape'] != 'text-node':
            continue
        a = box(c); lab = c['attrs']['label']
        if 'text' not in lab:
            continue
        f = font(lab['fontSize'], lab.get('fontWeight') == 'bold')
        if c.get('angle'):
            tw = int(dr.textlength(lab['text'], font=f)) + 12
            th = int(lab['fontSize'] * 1.9)
            tmp = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((4, 2), lab['text'], font=f, fill=lab.get('fill', '#1F2329'))
            tmp = tmp.rotate(-c['angle'], expand=True)
            im.paste(tmp, (int(a[0]), int(a[1])), tmp)
        else:
            txt = lab['text']
            maxw = a[2] - a[0]
            # 简单按宽度折行
            if maxw > 20 and dr.textlength(txt, font=f) > maxw:
                lines, cur = [], ''
                for ch in txt:
                    if dr.textlength(cur + ch, font=f) > maxw and cur:
                        lines.append(cur); cur = ch
                    else:
                        cur += ch
                if cur:
                    lines.append(cur)
            else:
                lines = [txt]
            ly = a[1]
            for ln_ in lines:
                dr.text((a[0], ly), ln_, font=f, fill=lab.get('fill', '#1F2329'))
                ly += lab['fontSize'] * (lab.get('lineHeight', lab['fontSize'] * 1.5) / lab['fontSize'])

    if S > 1:
        im = im.resize((W, H), Image.LANCZOS)
    im.save(out)
    print(out, im.size)


if __name__ == '__main__':
    import sys
    render(sys.argv[1], sys.argv[2])
