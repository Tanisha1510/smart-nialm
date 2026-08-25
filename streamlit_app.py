import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="HomePulse | Smart Energy Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS - MODERN LIVELY UI
# ============================================================
st.markdown("""
<style>

    .stApp {
        background: linear-gradient(135deg, #071426, #0b1f3a);
        color: white;
    }

    /* Main title */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 1.1rem;
        color: #a9b7d0;
        margin-bottom: 25px;
    }

    /* LIVE badge */
    .live-badge {
        background: #16c784;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }

    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        padding: 20px;
        border-radius: 18px;
        backdrop-filter: blur(10px);
        box-shadow: 0px 8px 25px rgba(0,0,0,0.25);
        transition: 0.3s;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #4cc9f0;
    }

    .metric-title {
        color: #a9b7d0;
        font-size: 0.9rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-top: 5px;
    }

    /* Appliance cards */
    .device-card {
        background: linear-gradient(
            145deg,
            rgba(255,255,255,0.10),
            rgba(255,255,255,0.04)
        );
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .device-name {
        font-size: 1.15rem;
        font-weight: bold;
    }

    .running {
        color: #16c784;
        font-weight: bold;
    }

    .off {
        color: #94a3b8;
        font-weight: bold;
    }

    h1, h2, h3 {
        color: white !important;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("⚙️ Home Control")

unit_rate = st.sidebar.number_input(
    "Electricity Tariff (₹/kWh)",
    min_value=1.0,
    max_value=20.0,
    value=7.5,
    step=0.5
)

simulate_live = st.sidebar.toggle(
    "🔴 Simulate Live Data",
    value=True
)

st.sidebar.divider()

st.sidebar.caption("🏠 HomePulse v1.0")
st.sidebar.caption("⚡ Smart Energy Intelligence")


# ============================================================
# APPLIANCE DATABASE
# ============================================================
appliances = [
    {"name": "Air Conditioner", "icon": "❄️", "room": "Bedroom", "base": 1450, "status": True},
    {"name": "Refrigerator", "icon": "🧊", "room": "Kitchen", "base": 180, "status": True},
    {"name": "Smart TV", "icon": "📺", "room": "Living Room", "base": 120, "status": True},
    {"name": "Ceiling Fan", "icon": "🌀", "room": "Bedroom", "base": 75, "status": True},
    {"name": "LED Lights", "icon": "💡", "room": "Living Room", "base": 45, "status": True},
    {"name": "Washing Machine", "icon": "🧺", "room": "Utility", "base": 650, "status": False},
    {"name": "Laptop", "icon": "💻", "room": "Study", "base": 90, "status": True},
    {"name": "Water Heater", "icon": "🚿", "room": "Bathroom", "base": 2000, "status": False},
    {"name": "Induction Cooktop", "icon": "🍳", "room": "Kitchen", "base": 1800, "status": False},
]


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []

if "energy" not in st.session_state:
    st.session_state.energy = {
        appliance["name"]: np.random.uniform(0.1, 2.5)
        for appliance in appliances
    }

if "runtime" not in st.session_state:
    st.session_state.runtime = {
        appliance["name"]: np.random.uniform(0.5, 8)
        for appliance in appliances
    }

if "statuses" not in st.session_state:
    st.session_state.statuses = {
        appliance["name"]: appliance["status"]
        for appliance in appliances
    }


# ============================================================
# LIVE POWER SIMULATION
# ============================================================
data = []

for appliance in appliances:

    name = appliance["name"]
    status = st.session_state.statuses[name]

    if simulate_live and np.random.random() > 0.97:
        status = not status
        st.session_state.statuses[name] = status

    if status:
        variation = np.random.normal(0, appliance["base"] * 0.05)
        power = max(5, appliance["base"] + variation)
    else:
        power = 0

    # Update energy and runtime
    if status:
        st.session_state.runtime[name] += 1 / 3600
        st.session_state.energy[name] += power / 1000 / 3600

    data.append({
        "Appliance": name,
        "Icon": appliance["icon"],
        "Room": appliance["room"],
        "Power (W)": round(power, 1),
        "Status": "🟢 ON" if status else "⚪ OFF",
        "Runtime (Hours)": round(st.session_state.runtime[name], 2),
        "Energy (kWh)": round(st.session_state.energy[name], 3)
    })


df = pd.DataFrame(data)

total_power = df["Power (W)"].sum()
total_energy = sum(st.session_state.energy.values())
total_cost = total_energy * unit_rate
devices_on = (df["Power (W)"] > 0).sum()


# ============================================================
# STORE LIVE HISTORY
# ============================================================
st.session_state.history.append({
    "Time": datetime.now(),
    "Total Power": total_power
})

# Keep recent 100 records
if len(st.session_state.history) > 100:
    st.session_state.history.pop(0)

history_df = pd.DataFrame(st.session_state.history)


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="main-title">🏠 HomePulse <span style="color:#4cc9f0;">⚡</span></div>
<div class="subtitle">
Smart Home Energy Intelligence • Monitor • Compare • Save
</div>
""", unsafe_allow_html=True)

st.markdown('<span class="live-badge">● LIVE ENERGY MONITORING</span>',
            unsafe_allow_html=True)

st.write("")


# ============================================================
# TOP METRICS
# ============================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">⚡ LIVE POWER</div>
        <div class="metric-value">{total_power/1000:.2f} kW</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🔋 ENERGY USED</div>
        <div class="metric-value">{total_energy:.2f} kWh</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">💰 ESTIMATED COST</div>
        <div class="metric-value">₹ {total_cost:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🟢 DEVICES RUNNING</div>
        <div class="metric-value">{devices_on} / {len(appliances)}</div>
    </div>
    """, unsafe_allow_html=True)


st.divider()


# ============================================================
# LIVE HOME APPLIANCES
# ============================================================
st.subheader("🏠 Live Home Appliances")

cols = st.columns(3)

for i, row in df.iterrows():

    with cols[i % 3]:

        status_class = "running" if row["Power (W)"] > 0 else "off"

        st.markdown(f"""
        <div class="device-card">
            <div class="device-name">
                {row["Icon"]} {row["Appliance"]}
            </div>

            <p>{row["Room"]}</p>

            <div class="{status_class}">
                {row["Status"]}
            </div>

            <h3>⚡ {row["Power (W)"]:.0f} W</h3>

            ⏱️ Runtime: <b>{row["Runtime (Hours)"]:.2f} hrs</b><br>
            🔋 Energy: <b>{row["Energy (kWh)"]:.3f} kWh</b>
        </div>
        """, unsafe_allow_html=True)


st.divider()


# ============================================================
# LIVE POWER + ENERGY COMPARISON
# ============================================================
left, right = st.columns(2)

with left:

    st.subheader("📈 Live Power Trend")

    if len(history_df) > 1:

        fig_live = px.line(
            history_df,
            x="Time",
            y="Total Power",
            markers=True
        )

        fig_live.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title="Time",
            yaxis_title="Power (W)"
        )

        st.plotly_chart(fig_live, use_container_width=True)

with right:

    st.subheader("⚡ Appliance Energy Comparison")

    fig_energy = px.bar(
        df.sort_values("Energy (kWh)", ascending=False),
        x="Appliance",
        y="Energy (kWh)",
        text="Energy (kWh)"
    )

    fig_energy.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_tickangle=-35
    )

    st.plotly_chart(fig_energy, use_container_width=True)


# ============================================================
# POWER COMPARISON
# ============================================================
st.subheader("🔌 Current Appliance Power Comparison")

fig_power = px.bar(
    df,
    x="Appliance",
    y="Power (W)",
    text="Power (W)"
)

fig_power.update_layout(
    template="plotly_dark",
    height=400,
    xaxis_tickangle=-30
)

st.plotly_chart(fig_power, use_container_width=True)


# ============================================================
# USAGE HISTORY TABLE
# ============================================================
st.subheader("📋 Today's Appliance Usage")

usage_df = df[[
    "Appliance",
    "Room",
    "Status",
    "Runtime (Hours)",
    "Energy (kWh)"
]].copy()

usage_df["Estimated Cost (₹)"] = (
    usage_df["Energy (kWh)"] * unit_rate
).round(2)

st.dataframe(
    usage_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SMART INSIGHT
# ============================================================
highest = df.loc[df["Energy (kWh)"].idxmax()]

st.info(
    f"💡 **Smart Insight:** {highest['Appliance']} is currently your "
    f"highest energy-consuming appliance with "
    f"**{highest['Energy (kWh)']:.2f} kWh** consumed."
)


# ============================================================
# AUTO REFRESH
# ============================================================
if simulate_live:
    time.sleep(3)
    st.rerun()
