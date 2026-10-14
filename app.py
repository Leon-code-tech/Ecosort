from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from waste_ops import classify_material, order_stops_nearest_neighbor, priority_label, priority_score


st.set_page_config(page_title="EcoSort | Waste Operations", page_icon="♻️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink: #18251f; --muted: #69766f; --green: #175e43; --lime: #d5f36a; --line: #e5ebe7; --paper: #f6f8f5; --orange: #d87842; }
    html, body, [class*="css"] { font-family: 'Manrope', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); }
    [data-testid="stSidebar"] { background: #18251f; border-right: 0; }
    [data-testid="stSidebar"] * { color: #f5f8f5; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: 7px 4px; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #b6c4bc; }
    .brand { font-size: 13px; letter-spacing: 0; font-weight: 800; color: #d5f36a; text-transform: uppercase; }
    .brand-mark { font-family: 'DM Mono', monospace; color: #d5f36a; font-size: 12px; margin-bottom: 7px; }
    .page-title { font-size: 31px; line-height: 1.15; font-weight: 800; margin: 0 0 5px; }
    .page-subtitle { color: #69766f; font-size: 14px; margin: 0 0 20px; }
    .eyebrow { font-family: 'DM Mono', monospace; font-size: 11px; text-transform: uppercase; color: #69766f; margin-bottom: 9px; }
    .metric-label { font-size: 12px; color: #69766f; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: 800; line-height: 1.15; color: #18251f; }
    .metric-note { font-size: 12px; color: #69766f; margin-top: 6px; }
    .metric-box { background: white; border: 1px solid #e5ebe7; border-radius: 6px; padding: 17px 18px; min-height: 111px; }
    .panel { background: white; border: 1px solid #e5ebe7; border-radius: 6px; padding: 18px 20px; }
    .panel-title { font-size: 16px; font-weight: 800; margin: 0 0 3px; }
    .panel-note { color: #69766f; font-size: 12px; margin-bottom: 14px; }
    .status-chip { display: inline-block; font-family: 'DM Mono', monospace; font-size: 11px; padding: 4px 8px; border-radius: 3px; background: #edf1ee; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #e5ebe7; border-radius: 6px; padding: 14px 16px; }
    div[data-testid="stMetricLabel"] { color: #69766f; }
    div[data-testid="stMetricValue"] { color: #18251f; }
    .stButton > button[kind="primary"] { background: #175e43; border-color: #175e43; color: white; }
    .stButton > button { border-radius: 4px; }
    hr { border-color: #e5ebe7; }
    @media (max-width: 700px) { .page-title { font-size: 25px; } .metric-box { min-height: 96px; padding: 13px; } .metric-value { font-size: 23px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

AREAS = ["Central", "Riverside", "Market", "Park"]
DEPOT = {"lat": 51.5077, "lon": -0.1180, "name": "Depot"}


def sample_bins():
    samples = [
        ("ES-104", "Central", "Mixed recycling", 92, 5, 51.5091, -0.1270),
        ("ES-108", "Central", "General waste", 64, 3, 51.5058, -0.1223),
        ("ES-112", "Central", "Food waste", 81, 6, 51.5120, -0.1160),
        ("ES-117", "Central", "Mixed recycling", 37, 2, 51.5039, -0.1125),
        ("ES-203", "Riverside", "General waste", 88, 6, 51.5060, -0.0950),
        ("ES-209", "Riverside", "Mixed recycling", 56, 4, 51.5016, -0.1031),
        ("ES-214", "Riverside", "Food waste", 29, 1, 51.5100, -0.0900),
        ("ES-218", "Riverside", "Mixed recycling", 97, 7, 51.4990, -0.0875),
        ("ES-301", "Market", "General waste", 73, 5, 51.5130, -0.1040),
        ("ES-306", "Market", "Food waste", 46, 3, 51.5150, -0.1090),
        ("ES-311", "Market", "Mixed recycling", 84, 6, 51.5170, -0.0980),
        ("ES-315", "Market", "General waste", 21, 1, 51.5100, -0.1010),
        ("ES-402", "Park", "Food waste", 68, 4, 51.5210, -0.1190),
        ("ES-407", "Park", "Mixed recycling", 32, 2, 51.5240, -0.1080),
        ("ES-413", "Park", "General waste", 91, 7, 51.5190, -0.1300),
        ("ES-419", "Park", "Food waste", 54, 3, 51.5270, -0.1240),
    ]
    columns = ["id", "area", "stream", "fill", "days", "lat", "lon"]
    return [dict(zip(columns, row)) for row in samples]


def current_bins():
    if "bins" not in st.session_state:
        st.session_state.bins = sample_bins()
    if "reports" not in st.session_state:
        st.session_state.reports = []
    return st.session_state.bins


def enriched_frame(bins):
    frame = pd.DataFrame(bins)
    frame["priority"] = frame.apply(lambda row: priority_score(row["fill"], row["days"]), axis=1)
    frame["urgency"] = frame["priority"].map(priority_label)
    return frame


def page_heading(title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def metric_box(label, value, note):
    st.markdown(
        f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def render_overview(frame):
    page_heading("Waste operations", "A live view of bin capacity and collection pressure across the district.")
    urgent_count = int((frame["urgency"] == "Urgent").sum())
    average_fill = int(round(frame["fill"].mean()))
    collected_today = sum(1 for row in current_bins() if row.get("days", 0) == 0)

    columns = st.columns(4)
    metrics = [
        ("CONNECTED BINS", f"{len(frame):02d}", "Across 4 service areas"),
        ("AVERAGE CAPACITY", f"{average_fill}%", "Network-wide fill level"),
        ("COLLECT SOON", f"{urgent_count:02d}", "Urgency score 75 or higher"),
        ("PICKED UP TODAY", f"{collected_today:02d}", "Simulated dispatches"),
    ]
    for column, (label, value, note) in zip(columns, metrics):
        with column:
            metric_box(label, value, note)

    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="panel-title">Capacity by service area</div><div class="panel-note">Average fill level · lower is healthier</div>', unsafe_allow_html=True)
        area_frame = frame.groupby("area", as_index=False)["fill"].mean()
        chart = px.bar(area_frame, x="area", y="fill", color="fill", color_continuous_scale=["#d5f36a", "#175e43"], range_color=[0, 100])
        chart.update_layout(height=280, margin=dict(l=0, r=0, t=8, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False, xaxis_title=None, yaxis_title="Fill %", font_family="Manrope", font_color="#69766f")
        chart.update_yaxes(range=[0, 100], gridcolor="#e5ebe7", zeroline=False)
        chart.update_xaxes(showgrid=False)
        st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    with right:
        st.markdown('<div class="panel-title">Collection queue</div><div class="panel-note">Highest urgency scores · review before dispatch</div>', unsafe_allow_html=True)
        queue = frame.sort_values("priority", ascending=False).head(6)
        display = queue[["id", "area", "stream", "fill", "priority"]].rename(columns={"id": "Bin", "area": "Area", "stream": "Stream", "fill": "Fill %", "priority": "Score"})
        st.dataframe(display, hide_index=True, width="stretch", height=280)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Network snapshot</div><div class="panel-note">Select an area to focus the monitoring view.</div>', unsafe_allow_html=True)
    area_filter = st.selectbox("Service area", ["All areas"] + AREAS, label_visibility="collapsed", key="overview_area")
    visible = frame if area_filter == "All areas" else frame[frame["area"] == area_filter]
    st.dataframe(
        visible[["id", "area", "stream", "fill", "days", "urgency"]].rename(columns={"id": "Bin ID", "area": "Area", "stream": "Waste stream", "fill": "Fill %", "days": "Days since pickup", "urgency": "Priority"}),
        hide_index=True,
        width="stretch",
    )


def render_bins(frame):
    page_heading("Bin network", "Monitor capacity and log a field report to update a bin.")
    area_filter = st.selectbox("Area", ["All areas"] + AREAS, key="network_area")
    visible = frame if area_filter == "All areas" else frame[frame["area"] == area_filter]
    st.dataframe(
        visible.sort_values("priority", ascending=False)[["id", "area", "stream", "fill", "days", "priority", "urgency"]].rename(columns={"id": "Bin ID", "area": "Area", "stream": "Waste stream", "fill": "Fill %", "days": "Days since pickup", "priority": "Score", "urgency": "Priority"}),
        hide_index=True,
        width="stretch",
    )

    st.markdown('<div class="panel-title">Report a bin</div><div class="panel-note">Reports update this browser session only.</div>', unsafe_allow_html=True)
    bins = current_bins()
    with st.form("bin_report"):
        first, second, third = st.columns([1, 1, 1.2])
        bin_id = first.selectbox("Bin ID", [row["id"] for row in bins])
        reported_fill = second.slider("Estimated fill", 0, 100, 80, format="%d%%")
        issue = third.selectbox("Field note", ["Near capacity", "Overflowing", "Contamination", "Damaged bin", "Other"])
        submitted = st.form_submit_button("Save report", type="primary")
    if submitted:
        for row in bins:
            if row["id"] == bin_id:
                row["fill"] = max(row["fill"], reported_fill)
                row["last_issue"] = issue
                break
        st.session_state.reports.insert(0, {"time": datetime.now().strftime("%H:%M"), "bin": bin_id, "issue": issue, "fill": reported_fill})
        st.success(f"Report saved for {bin_id}.")
        st.rerun()

    if st.session_state.reports:
        st.markdown('<div class="panel-title">Recent field reports</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.reports), hide_index=True, width="stretch")


def render_routes(frame):
    page_heading("Route planner", "Build a short pickup run from the bins with the most collection pressure.")
    first, second, third = st.columns([1, 1, 1.3])
    area = first.selectbox("Service area", AREAS, key="route_area")
    stop_limit = second.slider("Maximum stops", 2, 8, 5)
    include_low = third.toggle("Include all bins", value=False, help="By default, prioritize bins scoring 45 or higher.")

    candidates = frame[frame["area"] == area].copy()
    if not include_low:
        candidates = candidates[candidates["priority"] >= 45]
    candidates = candidates.sort_values("priority", ascending=False).head(stop_limit)
    if candidates.empty:
        st.info("No bins meet the current priority threshold in this area.")
        return

    stops = candidates.to_dict("records")
    route = order_stops_nearest_neighbor(stops, DEPOT)
    route_frame = pd.DataFrame(route)
    st.markdown(f'<div class="panel-title">{area} pickup run <span class="status-chip">{len(route)} stops</span></div><div class="panel-note">Suggested order uses straight-line distance from the depot. Confirm access and vehicle capacity before dispatch.</div>', unsafe_allow_html=True)

    left, right = st.columns([1.15, 1])
    with left:
        figure = go.Figure()
        path = [DEPOT] + route
        figure.add_trace(go.Scatter(x=[point["lon"] for point in path], y=[point["lat"] for point in path], mode="lines", line=dict(color="#99b3a4", width=2, dash="dot"), hoverinfo="skip", showlegend=False))
        figure.add_trace(go.Scatter(x=[DEPOT["lon"]], y=[DEPOT["lat"]], mode="markers+text", text=["DEPOT"], textposition="bottom center", marker=dict(size=14, color="#18251f", symbol="square"), name="Depot"))
        figure.add_trace(go.Scatter(x=route_frame["lon"], y=route_frame["lat"], mode="markers+text", text=[f"{index}. {stop['id']}" for index, stop in enumerate(route, start=1)], textposition="top center", marker=dict(size=13, color=route_frame["fill"], colorscale=[[0, "#d5f36a"], [1, "#d87842"]], cmin=0, cmax=100, line=dict(color="white", width=1)), name="Pickup"))
        figure.update_layout(height=360, margin=dict(l=5, r=5, t=18, b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f6f8f5", showlegend=False, font_family="Manrope", font_color="#69766f")
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    with right:
        ordered = pd.DataFrame([{ "Stop": index, "Bin": stop["id"], "Fill": f"{stop['fill']}%", "Score": stop["priority"] } for index, stop in enumerate(route, start=1)])
        st.dataframe(ordered, hide_index=True, width="stretch", height=360)
        if st.button("Dispatch pickup run", type="primary", width="stretch"):
            selected_ids = {stop["id"] for stop in route}
            for row in current_bins():
                if row["id"] in selected_ids:
                    row["fill"] = 12
                    row["days"] = 0
                    row.pop("last_issue", None)
            st.success(f"{len(selected_ids)} bins marked as collected.")
            st.rerun()


def render_sorting_guide():
    page_heading("Sorting guide", "Look up common items before they reach the wrong bin.")
    item = st.text_input("Item", placeholder="Try: AA battery, glass bottle, coffee grounds", label_visibility="collapsed")
    if item:
        category = classify_material(item)
        if category is None:
            st.warning("No confident match. Check your local council's waste guidance before disposal.")
        else:
            instructions = {
                "Hazardous": "Keep separate from household bins. Use a designated battery, household hazardous-waste, or pharmacy collection point as appropriate.",
                "Electronic": "Take to an electronics collection point or retailer take-back scheme. Remove personal data from devices first.",
                "Organic": "Use a food or garden-waste collection where available. Keep non-compostable packaging out.",
                "Recyclable": "Empty and rinse containers. Local rules vary, especially for plastics and cartons.",
                "General waste": "Place in residual waste unless your local service provides a dedicated take-back or specialist collection.",
            }
            st.success(f"Likely category: **{category}**")
            st.write(instructions[category])

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Quick reference</div><div class="panel-note">Common examples. Local acceptance rules can differ.</div>', unsafe_allow_html=True)
    reference = pd.DataFrame([
        ("Paper & cardboard", "Recyclable", "Keep clean and dry"),
        ("Glass bottles & jars", "Recyclable", "Empty; check whether lids are accepted"),
        ("Food scraps", "Organic", "Use food-waste service where available"),
        ("Batteries", "Hazardous", "Never put in general or recycling bins"),
        ("Phones & cables", "Electronic", "Use an e-waste or retailer take-back point"),
        ("Paint & chemicals", "Hazardous", "Use a household hazardous-waste site"),
    ], columns=["Material", "Likely category", "Handling"])
    st.dataframe(reference, hide_index=True, width="stretch")


bins = current_bins()
frame = enriched_frame(bins)

with st.sidebar:
    st.markdown('<div class="brand-mark">FIELD SYSTEM / 01</div><div class="brand">EcoSort</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("District operations", unsafe_allow_html=True)
    selected_page = st.radio("Workspace", ["Overview", "Bin network", "Route planner", "Sorting guide"], label_visibility="collapsed")
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("**NORTH DISTRICT**  \nSample network · 16 bins", unsafe_allow_html=True)
    st.markdown("Data is simulated and resets when the browser session ends.", unsafe_allow_html=True)

if selected_page == "Overview":
    render_overview(frame)
elif selected_page == "Bin network":
    render_bins(frame)
elif selected_page == "Route planner":
    render_routes(frame)
else:
    render_sorting_guide()
