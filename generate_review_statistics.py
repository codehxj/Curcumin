"""
Generate evidence-mapping figures for the curcumin CRC review.

The figures are derived from Curcumin_CRC_master_table_english_final.xlsx and
saved as 300 DPI PNG files in ./figures/.
"""
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "Curcumin_CRC_master_table_english_final.xlsx"
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
})


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = text.replace("NF-ŚĘB", "NF-kB")
    text = text.replace(" / ", "/")
    return text


def wrap_label(text, width=24):
    words = clean_text(text).split()
    lines, line = [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\n".join(lines)


def chapter_short(text):
    text = clean_text(text)
    text = re.sub(r"^Chapter\s+\d+:\s*", "", text)
    replacements = {
        "Research Basis and Application Limitations of Curcumin": "Basis & limitations",
        "Suppression of Malignant Biological Behaviors": "Malignant behavior",
        "Programmed Cell Death": "Cell death",
        "Signaling Pathways and Epigenetic Regulation": "Signaling & epigenetics",
        "Tumor Microenvironment, Immunity, and Gut Microbiota": "TME/immunity/microbiota",
        "Combination Therapy and Sensitization Strategies": "Combination therapy",
        "Formulation Optimization, Delivery Systems, and Structural Modification": "Delivery & modification",
        "Clinical Translation Prospects and Challenges": "Clinical translation",
        "Introduction and Background": "Introduction",
    }
    return replacements.get(text, text)


def save(fig, filename):
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {filename}")


df = pd.read_excel(DATA, sheet_name="Sheet1")
df = df[df["Statistical Inclusion Flag"].fillna("Include").isin(["Include", "Manual Check"])].copy()

for col in [
    "Primary Topic", "Study Type", "Evidence Level", "Review Chapter Assignment",
    "Writing Priority", "Primary Mechanistic Anchor", "Suitable for Main-text Citation",
    "Suitable for Figure/Table Support", "Figure/Table Support Level",
    "Published within the Last Five Years", "Hot Mechanism-related Paper",
    "High CRC Specificity",
]:
    df[col] = df[col].map(clean_text)

topic_order = df["Primary Topic"].value_counts().index.tolist()
topic_labels = [wrap_label(t, 22) for t in topic_order]


# Figure S1: topic-by-evidence stacked bars.
evidence_order = [
    "Preclinical Evidence",
    "Pre-translational Research",
    "Clinical Evidence",
    "Methodological/Formulation Optimization",
    "Mechanistic Review",
    "Clinical Perspective Discussion",
]
topic_ev = pd.crosstab(df["Primary Topic"], df["Evidence Level"]).reindex(topic_order).fillna(0)
topic_ev = topic_ev.reindex(columns=evidence_order, fill_value=0)
fig, ax = plt.subplots(figsize=(11, 6))
bottom = np.zeros(len(topic_ev))
colors = ["#356A9A", "#61A2A9", "#8BC28B", "#D7B45A", "#B57AA5", "#8F8F8F"]
for col, color in zip(topic_ev.columns, colors):
    vals = topic_ev[col].to_numpy()
    ax.bar(range(len(topic_ev)), vals, bottom=bottom, label=col, color=color, width=0.72)
    bottom += vals
ax.set_xticks(range(len(topic_ev)))
ax.set_xticklabels(topic_labels, rotation=45, ha="right")
ax.set_ylabel("Number of publications")
ax.set_title("Evidence maturity across curcumin CRC research topics")
ax.legend(ncol=2, frameon=False, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "evidence_by_topic.png")


# Figure S2: study-type composition by review chapter.
chapter_order = df["Review Chapter Assignment"].value_counts().index.tolist()
chapter_st = pd.crosstab(df["Review Chapter Assignment"].map(chapter_short), df["Study Type"])
chapter_st = chapter_st.reindex([chapter_short(c) for c in chapter_order]).fillna(0)
top_study_types = df["Study Type"].value_counts().head(6).index.tolist()
chapter_st = chapter_st.reindex(columns=top_study_types, fill_value=0)
fig, ax = plt.subplots(figsize=(10.5, 5.5))
bottom = np.zeros(len(chapter_st))
colors = ["#2F5D8C", "#4F9A94", "#E0A84C", "#9B7BB7", "#B65C5C", "#7A7A7A"]
for col, color in zip(chapter_st.columns, colors):
    vals = chapter_st[col].to_numpy()
    ax.bar(range(len(chapter_st)), vals, bottom=bottom, label=col, color=color, width=0.7)
    bottom += vals
ax.set_xticks(range(len(chapter_st)))
ax.set_xticklabels([wrap_label(x, 18) for x in chapter_st.index], rotation=45, ha="right")
ax.set_ylabel("Number of publications")
ax.set_title("Study-type composition mapped to review chapters")
ax.legend(ncol=2, frameon=False, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chapter_studytype_stack.png")


# Figure S3: leading mechanistic anchors.
anchor_counts = df["Primary Mechanistic Anchor"].replace("", np.nan).dropna().value_counts().head(20)
fig, ax = plt.subplots(figsize=(8.2, 6))
colors = plt.cm.viridis(np.linspace(0.25, 0.85, len(anchor_counts)))
ax.barh(range(len(anchor_counts)), anchor_counts.values, color=colors)
ax.set_yticks(range(len(anchor_counts)))
ax.set_yticklabels([wrap_label(x, 20) for x in anchor_counts.index])
ax.invert_yaxis()
ax.set_xlabel("Number of publications")
ax.set_title("Dominant mechanistic anchors in the curated evidence map")
for i, value in enumerate(anchor_counts.values):
    ax.text(value + 1, i, str(int(value)), va="center", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "mechanism_anchor_top20.png")


# Figure S4: recent and hot-mechanism signals by topic.
topic_recent = df.groupby("Primary Topic").agg(
    recent=("Published within the Last Five Years", lambda s: (s == "Yes").sum()),
    hot=("Hot Mechanism-related Paper", lambda s: (s == "Yes").sum()),
    total=("PMID", "count"),
).reindex(topic_order)
fig, ax = plt.subplots(figsize=(10.5, 5.5))
x = np.arange(len(topic_recent))
width = 0.35
ax.bar(x - width / 2, topic_recent["recent"], width, label="Published within last five years", color="#3E7CB1")
ax.bar(x + width / 2, topic_recent["hot"], width, label="Hot mechanism-related", color="#D27C44")
ax.plot(x, topic_recent["total"], color="#333333", marker="o", linewidth=1.5, label="Total")
ax.set_xticks(x)
ax.set_xticklabels(topic_labels, rotation=45, ha="right")
ax.set_ylabel("Number of publications")
ax.set_title("Recent activity and mechanistic hotspots by topic")
ax.legend(frameon=False, ncol=2)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "recent_hot_topic.png")


# Figure S5: figure/table support quality by topic.
support_order = [
    "A: Suitable for Core Figures/Tables in the Main Text",
    "B: Suitable for Supplementary Figures/Tables",
    "C: Suitable for Textual Support Only",
    "D: Not Recommended for Figure/Table Support",
]
support_labels = ["Core figure/table", "Supplementary", "Text support", "Not recommended"]
support = pd.crosstab(df["Primary Topic"], df["Figure/Table Support Level"]).reindex(topic_order).fillna(0)
support = support.reindex(columns=support_order, fill_value=0)
fig, ax = plt.subplots(figsize=(11, 6))
bottom = np.zeros(len(support))
colors = ["#245A83", "#63A377", "#C9A54D", "#9A9A9A"]
for col, label, color in zip(support.columns, support_labels, colors):
    vals = support[col].to_numpy()
    ax.bar(range(len(support)), vals, bottom=bottom, label=label, color=color, width=0.72)
    bottom += vals
ax.set_xticks(range(len(support)))
ax.set_xticklabels(topic_labels, rotation=45, ha="right")
ax.set_ylabel("Number of publications")
ax.set_title("Figure/table support level across research topics")
ax.legend(frameon=False, ncol=2)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "figure_support_by_topic.png")


# Figure S6: translational readiness dashboard by topic.
dash = df.groupby("Primary Topic").agg(
    clinical=("Evidence Level", lambda s: (s == "Clinical Evidence").sum()),
    core=("Suitable for Main-text Citation", lambda s: (s == "Yes").sum()),
    crc_specific=("High CRC Specificity", lambda s: (s == "Yes").sum()),
    high_priority=("Writing Priority", lambda s: (s == "High").sum()),
    total=("PMID", "count"),
).reindex(topic_order)
metrics = pd.DataFrame({
    "Clinical evidence (%)": dash["clinical"] / dash["total"] * 100,
    "Core citation (%)": dash["core"] / dash["total"] * 100,
    "CRC-specific (%)": dash["crc_specific"] / dash["total"] * 100,
    "High priority (%)": dash["high_priority"] / dash["total"] * 100,
}).fillna(0)
fig, ax = plt.subplots(figsize=(9.5, 6.2))
im = ax.imshow(metrics.to_numpy(), cmap="YlGnBu", aspect="auto", vmin=0, vmax=100)
ax.set_xticks(range(metrics.shape[1]))
ax.set_xticklabels(metrics.columns, rotation=30, ha="right")
ax.set_yticks(range(metrics.shape[0]))
ax.set_yticklabels([wrap_label(t, 24) for t in metrics.index])
for i in range(metrics.shape[0]):
    for j in range(metrics.shape[1]):
        value = metrics.iloc[i, j]
        ax.text(j, i, f"{value:.0f}", ha="center", va="center",
                color="white" if value > 55 else "#222222", fontsize=7)
ax.set_title("Translational readiness indicators by research topic")
cbar = fig.colorbar(im, ax=ax, shrink=0.72)
cbar.set_label("Percentage within topic")
save(fig, "translational_readiness_topic.png")
