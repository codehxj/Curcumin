"""
Generate publication-quality figures as SVG using pure Python (no external deps).
Output: 300 DPI equivalent PNG via cairosvg if available, or SVG directly.
"""
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
import os
import math

# ── Parse Excel ──
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ROOT = Path(__file__).resolve().parent
XLSX = ROOT / 'Curcumin_CRC_master_table_english_final.xlsx'

with zipfile.ZipFile(XLSX, 'r') as z:
    tree = ET.parse(z.open('xl/worksheets/sheet1.xml'))
    root = tree.getroot()
    def get_text(cell):
        if not cell: return ''
        is_elem = cell.find('.//s:is', ns)
        if is_elem is not None:
            t_elem = is_elem.find('.//s:t', ns)
            if t_elem is not None and t_elem.text: return t_elem.text.strip()
        v_elem = cell.find('s:v', ns)
        if v_elem is not None and v_elem.text: return v_elem.text.strip()
        return ''
    rows = root.findall('.//s:row', ns)
    records = []
    for row in rows[1:]:
        rnum = row.get('r')
        cells = {c.get('r'): c for c in row.findall('.//s:c', ns)}
        pmid = get_text(cells.get(f'A{rnum}', ''))
        if not pmid or not pmid.isdigit(): continue
        records.append({
            'year': get_text(cells.get(f'H{rnum}', '')),
            'topic': get_text(cells.get(f'Q{rnum}', '')),
            'evidence': get_text(cells.get(f'X{rnum}', '')),
            'study_type': get_text(cells.get(f'V{rnum}', '')),
        })

OUT = ROOT / 'figures'
os.makedirs(OUT, exist_ok=True)

# ── SVG helpers ──
def svg_header(w, h):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n<rect width="{w}" height="{h}" fill="white"/>\n'

def svg_footer():
    return '</svg>'

def svg_text(x, y, text, size=12, color='#333333', anchor='start', bold=False, rotate=0):
    fw = 'bold' if bold else 'normal'
    rot = f' transform="rotate({rotate},{x},{y})"' if rotate else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{fw}" font-family="Arial, Helvetica, sans-serif"{rot}>{text}</text>\n'

def svg_rect(x, y, w, h, fill='#2C6B9E', stroke='white', sw=0.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'

def svg_line(x1, y1, x2, y2, stroke='#cccccc', sw=1, dash=''):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>\n'

def svg_circle(cx, cy, r, fill='#C44E52'):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>\n'

def svg_path(d, stroke='#C44E52', sw=2, fill='none'):
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}"/>\n'

def save_svg(filename, content):
    path = os.path.join(OUT, filename)
    with open(path, 'w') as f:
        f.write(content)
    print(f'Generated: {filename}')

# ════════════════════════════════════════════════════
# 1. trend.svg — Annual Publication Trend
# ════════════════════════════════════════════════════
years = [r['year'] for r in records if r['year'].isdigit()]
year_counts = Counter(years)
sorted_years = sorted(int(y) for y in year_counts.keys())
counts = [year_counts[str(y)] for y in sorted_years]

W, H = 800, 450
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 60, 30, 50, 60
plot_w = W - MARGIN_L - MARGIN_R
plot_h = H - MARGIN_T - MARGIN_B

y_min, y_max = 0, max(counts) * 1.15
x_min, x_max = min(sorted_years) - 0.5, max(sorted_years) + 0.5

def x_scale(yv): return MARGIN_L + (yv - x_min) / (x_max - x_min) * plot_w
def y_scale(v): return MARGIN_T + plot_h - (v - y_min) / (y_max - y_min) * plot_h

svg = svg_header(W, H)
svg += f'<text x="{W/2}" y="30" font-size="14" font-weight="bold" text-anchor="middle" font-family="Arial">Annual Publication Trend of Curcumin in CRC Research</text>\n'

# Y axis grid lines
for v in range(0, int(y_max), 10):
    y = y_scale(v)
    svg += svg_line(MARGIN_L, y, W - MARGIN_R, y, '#e0e0e0', 0.5)
    svg += svg_text(MARGIN_L - 8, y + 4, str(v), 10, '#666666', 'end')

# Y axis label
svg += svg_text(15, H/2, 'Number of Publications', 11, '#333333', 'middle', rotate=-90)

# X axis
yr_step = max(1, (max(sorted_years) - min(sorted_years)) // 15)
for y in sorted_years:
    if (int(y) - min(int(vy) for vy in sorted_years)) % yr_step == 0 or y == max(sorted_years) or y == min(sorted_years):
        x = x_scale(int(y))
        svg += svg_line(x, MARGIN_T + plot_h, x, MARGIN_T + plot_h + 4, '#333333', 1)
        svg += svg_text(x, MARGIN_T + plot_h + 18, str(y), 9, '#666666', 'middle')

svg += svg_text(W/2, H - 5, 'Publication Year', 11, '#333333', 'middle')

# Bars
bar_w = plot_w / len(sorted_years) * 0.6
for i, (y, c) in enumerate(zip(sorted_years, counts)):
    x = x_scale(int(y)) - bar_w/2
    bh = y_scale(0) - y_scale(c)
    svg += svg_rect(x, y_scale(c), bar_w, bh, '#2C6B9E', 'white', 0.3)

# Line
points = []
for y, c in zip(sorted_years, counts):
    points.append(f'{x_scale(int(y))},{y_scale(c)}')
svg += svg_path('M ' + ' L '.join(points), '#C44E52', 1.5)

# Dots
for y, c in zip(sorted_years, counts):
    svg += svg_circle(x_scale(int(y)), y_scale(c), 3)

save_svg('trend.svg', svg)

# ════════════════════════════════════════════════════
# 2. topic.svg — Research Topic Distribution
# ════════════════════════════════════════════════════
topic_map = {
    'Malignant Biological Behaviors': 'Malignant Bio. Behaviors',
    'Formulation Optimization and Delivery Systems': 'Formulation & Delivery',
    'Programmed Cell Death': 'Programmed Cell Death',
    'Combination Therapy and Sensitization': 'Combination Therapy',
    'Signaling Pathways and Molecular Mechanisms': 'Signaling Pathways',
    'Derivatives and Structural Modification': 'Derivatives & Modification',
    'Overview and Research Background': 'Overview & Background',
    'Clinical Translation and Therapeutic Prospects': 'Clinical Translation',
    'Tumor Microenvironment and Immune Regulation': 'TME & Immune',
    'Epigenetics and Non-coding RNAs': 'Epigenetics & ncRNAs',
    'Gut Microbiota and Metabolism': 'Gut Microbiota',
    'Others': 'Others',
}
topics = [topic_map.get(r['topic'], r['topic']) for r in records if r['topic']]
topic_counts = Counter(topics)
sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

W2, H2 = 700, 480
MARGIN_L2, MARGIN_R2, MARGIN_T2, MARGIN_B2 = 180, 50, 50, 40
plot_w2 = W2 - MARGIN_L2 - MARGIN_R2
plot_h2 = H2 - MARGIN_T2 - MARGIN_B2

max_val = sorted_topics[0][1]
n_bars = len(sorted_topics)
bar_h = min(22, plot_h2 / n_bars - 3)

svg = svg_header(W2, H2)
svg += f'<text x="{W2/2}" y="28" font-size="14" font-weight="bold" text-anchor="middle" font-family="Arial">Distribution of Research Topics</text>\n'

for i, (name, val) in enumerate(sorted_topics):
    y = MARGIN_T2 + i * (bar_h + 4)
    bw = val / max_val * plot_w2
    # Color gradient
    intensity = 0.35 + 0.5 * (1 - i / n_bars)
    r = int(44 * intensity)
    g = int(107 * intensity)
    b = int(158 * intensity)
    color = f'#{r:02x}{g:02x}{b:02x}'
    svg += svg_rect(MARGIN_L2, y, bw, bar_h, color)
    svg += svg_text(MARGIN_L2 - 8, y + bar_h/2 + 4, name, 10, '#333333', 'end')
    svg += svg_text(MARGIN_L2 + bw + 5, y + bar_h/2 + 4, str(val), 9, '#666666', 'start')

svg += svg_text(MARGIN_L2 + plot_w2/2, H2 - 10, 'Number of Publications', 11, '#333333', 'middle')
save_svg('topic.svg', svg)

# ════════════════════════════════════════════════════
# 3. evidence.svg — Evidence Level Distribution
# ════════════════════════════════════════════════════
ev_map = {
    'Preclinical Evidence': 'Preclinical Evidence',
    'Clinical Evidence': 'Clinical Evidence',
    'Pre-translational Research': 'Pre-translational',
    'Methodological / Formulation Optimization': 'Methodological',
    'Mechanistic Review': 'Mechanistic Review',
    'Clinical Perspective Discussion': 'Clinical Perspective',
}
evidences = [ev_map.get(r['evidence'], r['evidence']) for r in records if r['evidence']]
ev_counts = Counter(evidences)
sorted_ev = sorted(ev_counts.items(), key=lambda x: x[1], reverse=True)

W3, H3 = 700, 350
MARGIN_L3, MARGIN_R3, MARGIN_T3, MARGIN_B3 = 80, 30, 50, 60
plot_w3 = W3 - MARGIN_L3 - MARGIN_R3
plot_h3 = H3 - MARGIN_T3 - MARGIN_B3

ev_colors = ['#2C6B9E', '#4C9AB8', '#6DB6A8', '#98D6A0', '#C7E9B4', '#F0F9E8']
n_ev = len(sorted_ev)
bar_w3 = min(50, plot_w3 / n_ev * 0.6)
total_w = n_ev * bar_w3 + (n_ev - 1) * 15
start_x = MARGIN_L3 + (plot_w3 - total_w) / 2

max_ev = sorted_ev[0][1]

svg = svg_header(W3, H3)
svg += f'<text x="{W3/2}" y="28" font-size="14" font-weight="bold" text-anchor="middle" font-family="Arial">Evidence Level Distribution</text>\n'

for i, (name, val) in enumerate(sorted_ev):
    x = start_x + i * (bar_w3 + 15)
    bh = val / max_ev * (plot_h3 - 30)
    svg += svg_rect(x, MARGIN_T3 + plot_h3 - bh, bar_w3, bh, ev_colors[i])
    svg += svg_text(x + bar_w3/2, MARGIN_T3 + plot_h3 - bh - 8, str(val), 10, '#333333', 'middle', bold=True)
    # X label with rotation
    label_y = MARGIN_T3 + plot_h3 + 15
    for j, ch in enumerate(name):
        svg += svg_text(x + bar_w3/2, label_y + j * 11, ch, 8, '#666666', 'middle')
    # Total line at bottom

svg += svg_text(W3/2, H3 - 5, 'Evidence Level', 11, '#333333', 'middle')
save_svg('evidence.svg', svg)

# ════════════════════════════════════════════════════
# 4. heatmap.svg — Topic × Year Heatmap
# ════════════════════════════════════════════════════
yt = defaultdict(lambda: defaultdict(int))
for r in records:
    y, t = r['year'], r['topic']
    if y.isdigit() and t:
        yt[int(y)][topic_map.get(t, t)] += 1

all_topics_ordered = [t[0] for t in Counter(
    topic_map.get(r['topic'], r['topic']) for r in records if r['topic']
).most_common()]

recent_years = [y for y in sorted(set(int(r['year']) for r in records if r['year'].isdigit())) if y >= 2005]

W4, H4 = 900, 500
MARGIN_L4, MARGIN_R4, MARGIN_T4, MARGIN_B4 = 160, 80, 50, 50
n_rows = len(all_topics_ordered)
n_cols = len(recent_years)
cell_w = min(25, (W4 - MARGIN_L4 - MARGIN_R4) / n_cols)
cell_h = min(22, (H4 - MARGIN_T4 - MARGIN_B4) / n_rows)
grid_w = cell_w * n_cols
grid_h = cell_h * n_rows
gx = MARGIN_L4
gy = MARGIN_T4

max_v = max((yt[y][t] for t in all_topics_ordered for y in recent_years), default=1)

svg = svg_header(W4, H4)
svg += f'<text x="{W4/2}" y="28" font-size="14" font-weight="bold" text-anchor="middle" font-family="Arial">Research Topic Distribution Over Time</text>\n'

for i, topic in enumerate(all_topics_ordered):
    for j, year in enumerate(recent_years):
        v = yt[year][topic]
        x = gx + j * cell_w
        y = gy + i * cell_h
        if v > 0:
            intensity = min(0.9, 0.1 + 0.8 * v / max_v)
            r = int(255 * (1 - intensity) + 44 * intensity)
            g = int(255 * (1 - intensity) + 107 * intensity)
            b = int(255 * (1 - intensity) + 158 * intensity)
            color = f'#{r:02x}{g:02x}{b:02x}'
        else:
            color = '#f5f5f5'
        svg += svg_rect(x, y, cell_w, cell_h, color, '#dddddd', 0.5)
        if v > 0:
            text_color = 'white' if v > max_v * 0.5 else '#333333'
            svg += svg_text(x + cell_w/2, y + cell_h/2 + 4, str(v), 8, text_color, 'middle')

# Row labels
for i, topic in enumerate(all_topics_ordered):
    svg += svg_text(gx - 8, gy + i * cell_h + cell_h/2 + 4, topic, 9, '#333333', 'end')

# Column labels
for j, year in enumerate(recent_years):
    svg += svg_text(gx + j * cell_w + cell_w/2, gy - 8, str(year), 8, '#666666', 'middle', rotate=45)

svg += svg_text(gx + grid_w/2, H4 - 10, 'Publication Year', 11, '#333333', 'middle')
svg += svg_text(12, gy + grid_h/2, 'Research Topic', 11, '#333333', 'middle', rotate=-90)

# Colorbar
cb_x = W4 - MARGIN_R4 + 15
cb_y = gy
cb_h = grid_h
cb_w = 12
for k in range(100):
    frac = k / 100
    r = int(255 * (1 - frac) + 44 * frac)
    g = int(255 * (1 - frac) + 107 * frac)
    b = int(255 * (1 - frac) + 158 * frac)
    color = f'#{r:02x}{g:02x}{b:02x}'
    y_pos = cb_y + cb_h * frac / 1.0
    svg += svg_rect(cb_x, y_pos, cb_w, cb_h/100 + 1, color, 'none')

svg += svg_text(cb_x + cb_w + 5, cb_y + 10, str(int(max_v)), 8, '#333333', 'start')
svg += svg_text(cb_x + cb_w + 5, cb_y + cb_h, '0', 8, '#333333', 'start')

save_svg('heatmap.svg', svg)

# ════════════════════════════════════════════════════
# 5. study_type.svg — Study Type Composition
# ════════════════════════════════════════════════════
st_map = {
    'In Vitro and In Vivo Study': 'In Vitro + In Vivo',
    'Clinical-related Study': 'Clinical-related',
    'Combination Therapy Study': 'Combination Therapy',
    'Formulation Study': 'Formulation',
    'In Vitro Study': 'In Vitro',
    'Review': 'Review',
    'Animal Study': 'Animal',
    'Systematic Review / Meta-analysis': 'Systematic Review/Meta',
    'Others': 'Others',
}
st_counts = Counter()
for r in records:
    s = r['study_type']
    if s:
        st_counts[st_map.get(s, s)] += 1
sorted_st = sorted(st_counts.items(), key=lambda x: x[1], reverse=True)

W5, H5 = 650, 380
MARGIN_L5, MARGIN_R5, MARGIN_T5, MARGIN_B5 = 160, 40, 50, 40
plot_w5 = W5 - MARGIN_L5 - MARGIN_R5
n_st = len(sorted_st)
bar_h5 = min(22, (H5 - MARGIN_T5 - MARGIN_B5) / n_st - 3)
max_st = sorted_st[0][1]

svg = svg_header(W5, H5)
svg += f'<text x="{W5/2}" y="28" font-size="14" font-weight="bold" text-anchor="middle" font-family="Arial">Study Type Composition</text>\n'

for i, (name, val) in enumerate(sorted_st):
    y = MARGIN_T5 + i * (bar_h5 + 4)
    bw = val / max_st * plot_w5
    intensity = 0.35 + 0.5 * (1 - i / n_st)
    r = int(44 * intensity); g = int(107 * intensity); b = int(158 * intensity)
    svg += svg_rect(MARGIN_L5, y, bw, bar_h5, f'#{r:02x}{g:02x}{b:02x}')
    svg += svg_text(MARGIN_L5 - 8, y + bar_h5/2 + 4, name, 9, '#333333', 'end')
    svg += svg_text(MARGIN_L5 + bw + 5, y + bar_h5/2 + 4, str(val), 9, '#666666', 'start')

save_svg('study_type.svg', svg)

print('\nAll SVG figures generated!')
