"""
Generate publication-quality data figures from curcumin CRC Excel data.
Output: 300 DPI PNG files in ./figures/
"""
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

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
            'chapter': get_text(cells.get(f'Z{rnum}', '')),
        })

OUT = ROOT / 'figures'
os.makedirs(OUT, exist_ok=True)

# ══════════════════════════════════════════
# Figure 1: Publication Year Trend (trend.png)
# ══════════════════════════════════════════
years = [int(r['year']) for r in records if r['year'].isdigit()]
year_counts = Counter(years)
sorted_years = sorted(year_counts.keys())
counts = [year_counts[y] for y in sorted_years]

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(sorted_years, counts, color='#2C6B9E', width=0.7, edgecolor='white', linewidth=0.3)
ax.plot(sorted_years, counts, color='#C44E52', marker='o', linewidth=1.5, markersize=4, zorder=5)
ax.set_xlabel('Publication Year', fontsize=11)
ax.set_ylabel('Number of Publications', fontsize=11)
ax.set_title('Annual Publication Trend of Curcumin in CRC Research', fontsize=12, fontweight='bold')
ax.set_xlim(min(sorted_years)-0.5, max(sorted_years)+0.5)
ax.xaxis.set_major_locator(ticker.MultipleLocator(3))
ax.tick_params(labelsize=9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(OUT / 'trend.png', dpi=300, bbox_inches='tight')
plt.close()
print('Generated: trend.png')

# ══════════════════════════════════════════
# Figure 2: Research Topic Distribution (topic.png)
# ══════════════════════════════════════════
topic_map = {
    'Malignant Biological Behaviors': 'Malignant Biological\nBehaviors',
    'Formulation Optimization and Delivery Systems': 'Formulation &\nDelivery Systems',
    'Programmed Cell Death': 'Programmed\nCell Death',
    'Combination Therapy and Sensitization': 'Combination Therapy\n& Sensitization',
    'Signaling Pathways and Molecular Mechanisms': 'Signaling Pathways\n& Molecular Mechanisms',
    'Derivatives and Structural Modification': 'Derivatives &\nStructural Modification',
    'Overview and Research Background': 'Overview &\nResearch Background',
    'Clinical Translation and Therapeutic Prospects': 'Clinical Translation\n& Therapeutic Prospects',
    'Tumor Microenvironment and Immune Regulation': 'TME &\nImmune Regulation',
    'Epigenetics and Non-coding RNAs': 'Epigenetics &\nNon-coding RNAs',
    'Gut Microbiota and Metabolism': 'Gut Microbiota\n& Metabolism',
    'Others': 'Others',
}

topics = [topic_map.get(r['topic'], r['topic']) for r in records if r['topic']]
topic_counts = Counter(topics)
sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

fig, ax = plt.subplots(figsize=(8, 5))
names = [t[0] for t in sorted_topics]
vals = [t[1] for t in sorted_topics]
colors = plt.cm.Blues(np.linspace(0.4, 0.85, len(names)))[::-1]
bars = ax.barh(range(len(names)), vals, color=colors, edgecolor='white', height=0.65)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel('Number of Publications', fontsize=11)
ax.set_title('Distribution of Research Topics', fontsize=12, fontweight='bold')
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, str(v),
            va='center', fontsize=8, color='#333333')
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(labelsize=9)
plt.tight_layout()
plt.savefig(OUT / 'topic.png', dpi=300, bbox_inches='tight')
plt.close()
print('Generated: topic.png')

# ══════════════════════════════════════════
# Figure 3: Evidence Level Distribution (evidence.png)
# ══════════════════════════════════════════
ev_map = {
    'Preclinical Evidence': 'Preclinical\nEvidence',
    'Clinical Evidence': 'Clinical\nEvidence',
    'Pre-translational Research': 'Pre-translational\nResearch',
    'Methodological / Formulation Optimization': 'Methodological /\nFormulation',
    'Mechanistic Review': 'Mechanistic\nReview',
    'Clinical Perspective Discussion': 'Clinical\nPerspective',
}
evidences = [ev_map.get(r['evidence'], r['evidence']) for r in records if r['evidence']]
ev_counts = Counter(evidences)
sorted_ev = sorted(ev_counts.items(), key=lambda x: x[1], reverse=True)

fig, ax = plt.subplots(figsize=(8, 4))
names_ev = [e[0] for e in sorted_ev]
vals_ev = [e[1] for e in sorted_ev]
bar_colors = ['#2C6B9E', '#4C9AB8', '#6DB6A8', '#98D6A0', '#C7E9B4', '#F0F9E8'][:len(names_ev)]
bars = ax.bar(range(len(names_ev)), vals_ev, color=bar_colors, edgecolor='white', width=0.6)
ax.set_xticks(range(len(names_ev)))
ax.set_xticklabels(names_ev, fontsize=9, rotation=15, ha='right')
ax.set_ylabel('Number of Publications', fontsize=11)
ax.set_title('Evidence Level Distribution of Curcumin CRC Studies', fontsize=12, fontweight='bold')
for bar, v in zip(bars, vals_ev):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(v),
            ha='center', fontsize=9, fontweight='bold', color='#333333')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(labelsize=9)
plt.tight_layout()
plt.savefig(OUT / 'evidence.png', dpi=300, bbox_inches='tight')
plt.close()
print('Generated: evidence.png')

# ══════════════════════════════════════════
# Figure 4: Topic × Year Heatmap (heatmap.png)
# ══════════════════════════════════════════
yt = defaultdict(lambda: defaultdict(int))
for r in records:
    y, t = r['year'], r['topic']
    if y.isdigit() and t:
        t_short = topic_map.get(t, t)
        yt[int(y)][t_short] += 1

all_years = sorted(set(int(r['year']) for r in records if r['year'].isdigit()))
all_topics_ordered = [t[0] for t in Counter(
    topic_map.get(r['topic'], r['topic']) for r in records if r['topic']
).most_common()]

# Filter to last 20 years for readability
recent_years = [y for y in all_years if y >= 2005]
heat_data = np.zeros((len(all_topics_ordered), len(recent_years)))
for i, t in enumerate(all_topics_ordered):
    for j, y in enumerate(recent_years):
        heat_data[i, j] = yt[y][t]

fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(heat_data, aspect='auto', cmap='Blues', interpolation='nearest')
ax.set_xticks(range(len(recent_years)))
ax.set_xticklabels(recent_years, fontsize=8, rotation=45, ha='right')
ax.set_yticks(range(len(all_topics_ordered)))
ax.set_yticklabels(all_topics_ordered, fontsize=8)
ax.set_xlabel('Publication Year', fontsize=11)
ax.set_ylabel('Research Topic', fontsize=11)
ax.set_title('Research Topic Distribution Over Time', fontsize=12, fontweight='bold')

for i in range(len(all_topics_ordered)):
    for j in range(len(recent_years)):
        v = heat_data[i, j]
        if v > 0:
            ax.text(j, i, int(v), ha='center', va='center', fontsize=6,
                   color='white' if v > heat_data.max()/2 else '#333333')

cbar = plt.colorbar(im, ax=ax, shrink=0.6)
cbar.set_label('Number of Publications', fontsize=9)
plt.tight_layout()
plt.savefig(OUT / 'heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print('Generated: heatmap.png')

# ══════════════════════════════════════════
# Figure 5: Study Type Composition (study_type.png)
# ══════════════════════════════════════════
st_map = {
    'In Vitro and In Vivo Study': 'In Vitro + In Vivo',
    'Clinical-related Study': 'Clinical-related',
    'Combination Therapy Study': 'Combination Therapy',
    'Formulation Study': 'Formulation',
    'In Vitro Study': 'In Vitro',
    'Review': 'Review',
    'Animal Study': 'Animal Study',
    'Systematic Review / Meta-analysis': 'Systematic Review/\nMeta-analysis',
    'Others': 'Others',
}
st_counts = Counter()
for r in records:
    s = r['study_type']
    if s:
        st_counts[st_map.get(s, s)] += 1
sorted_st = sorted(st_counts.items(), key=lambda x: x[1], reverse=True)

fig, ax = plt.subplots(figsize=(7, 4))
names_st = [s[0] for s in sorted_st]
vals_st = [s[1] for s in sorted_st]
st_colors = plt.cm.Blues(np.linspace(0.35, 0.85, len(names_st)))[::-1]
bars = ax.barh(range(len(names_st)), vals_st, color=st_colors, edgecolor='white', height=0.6)
ax.set_yticks(range(len(names_st)))
ax.set_yticklabels(names_st, fontsize=9)
ax.set_xlabel('Number of Publications', fontsize=11)
ax.set_title('Study Type Composition', fontsize=12, fontweight='bold')
for bar, v in zip(bars, vals_st):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, str(v),
            va='center', fontsize=8, color='#333333')
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(OUT / 'study_type.png', dpi=300, bbox_inches='tight')
plt.close()
print('Generated: study_type.png')

print('\nAll figures generated successfully!')
