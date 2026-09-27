import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Lebanon's Commercial Landscape", layout="wide")

SMALL = "Total number of commercial institutions by size - number of small institutions"
MEDIUM = "Total number of commercial institutions by size - number of medium-sized institutions"
LARGE = "Total number of commercial institutions by size - number of large-sized institutions"
SERVICE = "Total number of service institutions"


def fix_text(s):
    try:
        return s.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


@st.cache_data
def load_data():
    df = pd.read_csv("commercial_institutions.csv")
    df.columns = df.columns.str.strip()
    df["Region"] = (
        df["refArea"].str.split("/").str[-1]
        .str.replace("_", " ")
        .apply(fix_text)
        .str.replace(", Lebanon", "")
    )
    df["Town"] = df["Town"].apply(fix_text)
    df["Total"] = df[SMALL] + df[MEDIUM] + df[LARGE]
    return df


df = load_data()
active = df[df["Total"] > 0]

st.title("Lebanon's commercial activity is concentrated in a few towns")
st.markdown(f"""
After the 2019 financial crisis, the Lebanese lira lost its 1,507.5 LBP/USD peg.
This page uses town-level data on commercial institutions to show how the country's commercial activity is concentrated in a few towns, and how that concentration varies across regions.
Each row is a town, with its number of small, medium and large institutions.
{len(df) - len(active):,} of the {len(df):,} towns report no institutions at all,
so the charts show only the {len(active):,} active towns.

**How to use:** choose regions to compare in the sidebar, then zoom into one of them.
""")
region_order = (
    active.groupby("Region")["Total"].sum()
    .sort_values(ascending=False).index.tolist()
)

st.sidebar.header("Explore")
regions = st.sidebar.multiselect(
    "1. Regions to compare",
    region_order,
    default=region_order[:8],
)

if not regions:
    st.warning("Select at least one region.")
    st.stop()
focus = st.sidebar.selectbox(
    "2. Zoom into one region",
    ["All selected regions"] + regions,
)

compare_df = active[active["Region"].isin(regions)]
if focus == "All selected regions":
    focus_df = compare_df
else:
    focus_df = compare_df[compare_df["Region"] == focus]

k1, k2, k3 = st.columns(3)
k1.metric("Active towns", len(focus_df))
k2.metric("Commercial institutions", f"{focus_df['Total'].sum():,}")

top = focus_df.loc[focus_df["Total"].idxmax()]
k3.metric(
    "Share held by biggest town",
    f"{top['Total'] / focus_df['Total'].sum():.0%}",
    top["Town"],
    delta_color="off",
)
left, right = st.columns(2)

box_df = compare_df.copy()
box_df["Highlight"] = np.where(box_df["Region"] == focus, "Focus", "Other")

fig_box = px.box(
    box_df,
    x="Region",
    y="Total",
    color="Highlight" if focus != "All selected regions" else None,
    color_discrete_map={"Focus": "#E45756", "Other": "#BAB0AC"},
    category_orders={"Region": regions},
    log_y=True,
    points="outliers",
    hover_name="Town",
    labels={"Total": "Institutions per town (log scale)", "Region": ""},
    title="How evenly are institutions spread across each region's towns?",
)
fig_box.update_layout(showlegend=False, boxmode="overlay")
left.plotly_chart(fig_box, width="stretch")
sc = focus_df.copy()
sc["Medium (log)"] = np.log1p(sc[MEDIUM])
sc["Large (log)"] = np.log1p(sc[LARGE])

fig_sc = px.scatter(
    sc,
    x="Medium (log)",
    y="Large (log)",
    size=SERVICE,
    color=SERVICE,
    size_max=40,
    hover_name="Town",
    hover_data={"Region": True, MEDIUM: True, LARGE: True},
    labels={SERVICE: "Service institutions"},
    title=f"Medium vs. large institutions by town: {focus}",
)
right.plotly_chart(fig_sc, width="stretch")
st.subheader("Key insights")
st.markdown("""
**Big Idea: Lebanon's commercial activity is concentrated in a handful of towns, 
so regional totals can hide how much each region depends on a single commerical hub.**

1. **A few towns carry the country.** Only 10 of Lebanon's 1,137 towns hold **48%** of all
   42,436 recorded commercial institutions. The top three alone (Saadnayel, Baalbek and Chiyah)
   hold over 12,000.

2. **Big regional totals can hide a single town.** Zoom into Baalbek-Hermel and the city of
   **Baalbek holds 75%** of the region's institutions. In Baabda District, **Chiyah holds 80%**.
   Zahlé District has the highest total, but Saadnayel alone accounts for **47%** of it.

3. **The biggest region is not the one with the busiest typical town.** Sidon District has
   the **highest median** (about 103 institutions per active town), more than double Zahlé's
   (about 48). Sidon's activity is spread across many mid-sized towns instead of one hub.

4. **Matn District has the most balanced and least small-scale mix.** Its largest town
   (Bsalim) holds only **17%** of the region's institutions, and just **71%** are small,
   compared with **92%** nationally. In the scatter plot, its towns sit higher on both the
   medium and large axes.
""")
with st.expander("Design justification: region multiselect"):
    st.markdown("""
**User question:** How do Lebanon's main regions compare in how commercial activity is spread
across their towns? Is a region's activity shared by many towns or concentrated in a few?

**Why this widget:** I chose a multiselect because the question is about comparing regions,
and a single-select dropdown would show only one box at a time, leaving nothing to compare.
I also considered showing all 25 regions without a widget, but that made the box plot cluttered
and hard to read. The multiselect starts with the 8 largest regions and lets the user add or
remove regions.

**Course concept:** This follows the difference between exploratory and explanatory analysis.
Instead of showing all the data I went through, the default view presents only what the audience
needs to see first which are the 8 regions that hold about 75% of all institutions. It also reflects the
mechanism idea: an app is closer to a written document than a live presentation, because
the audience controls how they consume the information. They therefore need the option to
explore more detail (other regions) without me being there to explain.
""")

with st.expander("Design justification: zoom dropdown"):
    st.markdown("""
**User question:** Within one region, which towns drive the activity, and do towns with more
medium-sized institutions also have more large ones?

**Why this widget:** I used a single-select dropdown because only one region can be the focus
at a time. A second multiselect would allow overlapping or contradictory choices. Its options
come only from the regions chosen in the first widget, so the user drills down from an overview
into one region rather than filtering two unrelated things. I considered clicking directly on
the box plot, but a dropdown is clearer and easier to discover for first-time users.

**Course concept:** This follows the "who, what, how" framework. For a reader who wants to
understand a specific region, it shows that the regional total often depends on one town
, and by using the town-level data behind the box plot. Context is kept while focusing
attention by having the chosen region turn to red while the other regions stay grey in the box plot, and
the metric "Share held by biggest town" states the key message as a single number.
""")
