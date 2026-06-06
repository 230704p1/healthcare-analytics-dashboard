import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    layout="wide"
)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("HHS_chaildren_helthcare_cleaned_dataset.csv")
    df["Date"] = pd.to_datetime(df["Date"])

    df["Total System Load"] = (
        df["Children in CBP custody"]
        + df["Children in HHS Care"]
    )

    df["Net Intake"] = (
        df["Children transferred out of CBP custody"]
        - df["Children discharged from HHS Care"]
    )

    return df

df = load_data()

# =========================
# CSS
# =========================
st.markdown("""
<style>

.kpi-card{
    background: linear-gradient(135deg,#0f172a,#1e293b);
    border-radius:20px;
    padding:25px;
    text-align:center;
    color:white;
    min-height:180px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    box-shadow:0 10px 25px rgba(0,0,0,0.25);
    border:1px solid rgba(255,255,255,0.1);
    transition:all 0.3s ease;
}

.kpi-card:hover{
    transform:translateY(-6px);
    box-shadow:0 15px 35px rgba(37,99,235,0.4);
}

.kpi-title{
    font-size:16px;
    color:#cbd5e1;
    font-weight:600;
    margin-bottom:10px;
}

.kpi-value{
    font-size:34px;
    font-weight:700;
    color:#38bdf8;
}

div[data-testid="stSidebar"]{
    background-color:#0f172a;
}

div[data-testid="stSidebar"] *{
    color:white;
}

</style>
""", unsafe_allow_html=True)
# =========================
# HEADER
# =========================
st.markdown("""
<h1 style='text-align:center;color:#0F766E;'>
🏥 Healthcare Capacity Analytics Dashboard
</h1>
<h4 style='text-align:center;color:gray;'>
System Capacity & Care Load Analytics for Unaccompanied Children
</h4>
""", unsafe_allow_html=True)

st.markdown("---")

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.title("📅 Dashboard Filters")

start_date = st.sidebar.date_input(
    "Start Date",
    value=df["Date"].min().date()
)

end_date = st.sidebar.date_input(
    "End Date",
    value=df["Date"].max().date()
)

filtered_df = df[
    (df["Date"] >= pd.to_datetime(start_date))
    &
    (df["Date"] <= pd.to_datetime(end_date))
]

# No data check
if filtered_df.empty:
    st.warning("No data available for selected date range")
    st.stop()

selected_metrics = st.sidebar.multiselect(
    "Select Metrics",
    [
        "Children in CBP custody",
        "Children in HHS Care",
        "Total System Load",
        "Net Intake"
    ],
    default=["Total System Load"]
)

filtered_df["Growth Rate"] = (
    filtered_df["Total System Load"]
    .pct_change() * 100
)

filtered_df["Backlog Indicator"] = (
    filtered_df["Net Intake"]
    .rolling(14)
    .mean()
)

granularity = st.sidebar.selectbox(
    "Time Granularity",
    ["Daily", "Weekly", "Monthly"]
)

if granularity == "Daily":
    chart_df = filtered_df.copy()

elif granularity == "Weekly":
    chart_df = (
        filtered_df
        .groupby(pd.Grouper(key="Date", freq="W"))
        .mean(numeric_only=True)
        .reset_index()
    )

else:  # Monthly
    chart_df = (
        filtered_df
        .groupby(pd.Grouper(key="Date", freq="M"))
        .mean(numeric_only=True)
        .reset_index()
    )
# =========================
# KPI SECTION
# =========================

total_load = int(filtered_df["Total System Load"].mean())
avg_hhs = int(filtered_df["Children in HHS Care"].mean())
avg_cbp = int(filtered_df["Children in CBP custody"].mean())
net_intake = int(filtered_df["Net Intake"].mean())
if len(filtered_df) >= 14:
    backlog = round(
        filtered_df["Net Intake"]
        .rolling(14)
        .mean()
        .iloc[-1],
        1
    )
else:
    backlog = 0

# ---------- ROW 1 ----------

col1, col2, col3 ,col4,col5= st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">🏥 Total Chaildren Under Care</div>
        <div class="kpi-value">{total_load:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">👨‍⚕️ Average HHS Care</div>
        <div class="kpi-value">{avg_hhs:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">🚔 Average CBP Custody</div>
        <div class="kpi-value">{avg_cbp:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">📦 Net Intake Pressure</div>
        <div class="kpi-value">{net_intake:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">📈 Backlog Accumulation Rate</div>
        <div class="kpi-value">{backlog}</div>
    </div>
    """, unsafe_allow_html=True)
# =========================
# MONTHLY DATA
# =========================

monthly = (
    filtered_df
    .groupby(filtered_df["Date"].dt.to_period("M"))
    .mean(numeric_only=True)
)

monthly.index = monthly.index.astype(str)

# =========================
# CHART SELECTOR
# =========================

chart_option = st.selectbox(
    "📊 Select Chart",
    [
        "Total System Load",
        "HHS Care Trend",
        "CBP Custody Trend",
        "Net Intake Trend",
        "Discharge Trend"
    ]
)
if chart_option == "Total System Load":

    fig = px.line(
        chart_df,
        x="Date",
        y="Total System Load",
        title="Monthly Average Total System Load",
        color_discrete_sequence=["#00E5FF"]
    )

elif chart_option == "HHS Care Trend":


    fig = px.line(
    chart_df,
    x="Date",
    y="Children in HHS Care",
    title="HHS Care Trend"
    )

    fig.update_traces(
    line=dict(color="#703107", width=4)
)

    fig.update_layout(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white"
)

elif chart_option == "CBP Custody Trend":

    fig = px.line(
    chart_df,
    x="Date",
    y="Children in CBP custody",  
    title="CBP Custody Trend",
    color_discrete_sequence=["#00E5FF"]
)

    fig.update_traces(
    line=dict(color="#F59E0B", width=4)
)

    fig.update_layout(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white"
)
elif chart_option == "Net Intake Trend":

    fig = px.line(
        chart_df,
        x="Date",
        y="Net Intake",
        title="Net Intake Trend"
    )

    fig.update_traces(
        line=dict(
            color="#DE191C",
            width=2
        )
    )
else:

    discharge = (
        chart_df
        .groupby(
            chart_df["Date"].dt.to_period("M")
        )[
            "Children discharged from HHS Care"
        ]
        .mean()
    )

    discharge.index = discharge.index.astype(str)

    fig = px.line(
        x=discharge.index,
        y=discharge.values,
        title="Monthly Average Discharge Trend"
    )

    fig.update_traces(
        line=dict(
            color="#14B81F",
            width=4
        )
    )
# GRAPH SHOW

fig.update_layout(
    height=550
)
fig.update_layout(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white",
    title_font_size=22
)
st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================
# CHILDREN APPREHENDED
# =========================

st.subheader(
    "👶 Children Apprehended"
)

fig_app = px.bar(
    filtered_df.head(20),
    x="Date",
    y="Children apprehended and placed in CBP custody*",
    title="Children Apprehended",
     color="Children apprehended and placed in CBP custody*",
    color_continuous_scale=["#22C55E", "#38BDF8","#F97316"]
)


fig_app.update_layout(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white",
    title_font_size=22
)
st.plotly_chart(
    fig_app,
    use_container_width=True
)
# =========================
# SCATTER CHART
# =========================

st.subheader(
    "⚖️ CBP vs HHS Comparison"
)

fig1 = px.scatter(
    filtered_df,
    x="Children in CBP custody",
    y="Children in HHS Care",
    title="CBP vs HHS Comparison",
    color="Children in HHS Care",
    color_continuous_scale="Viridis",
)

fig1.update_traces(
    marker=dict(
        size=10,
        line=dict(width=1, color="white")
    )
)

fig1.update_layout(
    height=600,
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white",
    title_font_size=22
)
st.plotly_chart(
    fig1,
    use_container_width=True
)

# =========================
# FULL WIDTH HEATMAP
# =========================

st.subheader("🔥 Correlation Heatmap")

corr = filtered_df.select_dtypes(include="number").corr()

fig2 = px.imshow(
    corr,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale="RdBu_r"
)

fig2.update_layout(
    height=700
)

fig2.update_layout(
    height=700,
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white"
)
st.plotly_chart(
    fig2,
    use_container_width=True
)
# =========================
# CHART 6 - HHS DISTRIBUTION
# =========================

st.subheader("📊 HHS Care Distribution")

fig3 = px.histogram(
    filtered_df,
    x="Children in HHS Care",
    nbins=20,
    title="Distribution of HHS Care",
    color_discrete_sequence=["#A855F7",]
)
fig3.update_traces(
    marker_line_color="white",
    marker_line_width=1
)
fig3.update_layout(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white",
    title_font_size=22,
    height=600
)
st.plotly_chart(fig3, use_container_width=True)



# =========================
# CHART 8 - DISCHARGE BAR
# =========================

st.subheader("📦 Monthly Discharge Analysis")

monthly_discharge = (
    filtered_df
    .groupby(
        filtered_df["Date"].dt.to_period("M")
    )[
        "Children discharged from HHS Care"
    ]
    .mean()
    .reset_index()
)

monthly_discharge = (
    monthly_discharge
    .sort_values(
        by="Date",
        ascending=True
    )
)

monthly_discharge["Date"] = (
    monthly_discharge["Date"]
    .astype(str)
)

fig5 = px.bar(
    monthly_discharge,
    x="Date",
    y="Children discharged from HHS Care",
    title="Monthly Average Discharge",
    color="Children discharged from HHS Care",
    color_continuous_scale=[
        "#22C55E",  # Green
        "#38BDF8",  # Blue
        "#A855F7"   # Purple
    ]
)

fig5.update_traces(
    marker_line_color="white",
    marker_line_width=1
)

fig5.update_layout(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="white",
    title_font_size=22,
    height=600
)

st.plotly_chart(
    fig5,
    use_container_width=True
)
# =========================
# INSIGHTS
# =========================
st.subheader("📌 Key Insights")

st.info("""
• Total System Load increased significantly during peak periods.

• HHS Care contributes the largest share of overall care burden.

• Positive relationship exists between CBP Custody and HHS Care.

• Net Intake spikes indicate capacity stress periods.

• Higher discharge rates help reduce backlog accumulation.
""")


csv = filtered_df.to_csv(index=False)

st.download_button(
    label="📥 Download Filtered Dataset",
    data=csv,
    file_name="Healthcare_Analytics_Report.csv",
    mime="text/csv"
)
# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Developed by Priyal Patel | Unified Mentor Internship Project")
