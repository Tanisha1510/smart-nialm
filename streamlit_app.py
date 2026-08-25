import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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

    .metric-delta-up { color: #ff6b6b; font-size: 0.85rem; }
    .metric-delta-down { color: #16c784; font-size: 0.85rem; }

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

    .running { color: #16c784; font-weight: bold; }
    .off { color: #94a3b8; font-weight: bold; }

    .alert-card {
        background: rgba(255,107,107,0.12);
        border: 1px solid rgba(255,107,107,0.4);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 8px;
    }

    h1, h2, h3 { color: white !important; }

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("⚙️ Home Control")

unit_rate = st.sidebar.number_input(
    "Electricity Tariff (₹/kWh)", min_value=1.0, max_value=20.0,
    value=7.5, step=0.5
)

house_capacity_kw = st.sidebar.slider(
    "Sanctioned Load Capacity (kW)", min_value=2.0, max_value=15.0,
    value=6.0, step=0.5
)

sim_speed = st.sidebar.select_slider(
    "⏩ Simulation Speed (sim-minutes / refresh)",
    options=[5, 15, 30, 60, 120],
    value=30
)

simulate_live = st.sidebar.toggle("🔴 Simulate Live Data", value=True)

st.sidebar.divider()
st.sidebar.caption("🏠 HomePulse v2.0")
st.sidebar.caption("⚡ Smart Energy Intelligence")
st.sidebar.caption("Powered by predefined 24-hour appliance load profiles")


# ============================================================
# APPLIANCE DATABASE — WITH PREDEFINED 24-HOUR LOAD PROFILES
# Each profile is a multiplier (0–1) of the appliance's rated
# power for every hour of the day. This replaces pure randomness
# with realistic, fed-in usage patterns that still evolve live.
# ============================================================
def profile(pattern):
    """Expand a 24-value list into a numpy array."""
    return np.array(pattern, dtype=float)

appliances = [
    {
        "name": "Air Conditioner", "icon": "❄️", "room": "Bedroom", "base": 1450,
        "profile": profile([0,0,0,0,0,0,0,0,0,0,0,0,0.2,0.3,0.4,0.5,0.4,0.2,
                             0.6,0.9,1.0,1.0,0.9,0.3])
    },
    {
        "name": "Refrigerator", "icon": "🧊", "room": "Kitchen", "base": 180,
        "profile": profile([0.6]*24)  # near-constant cyclic load
    },
    {
        "name": "Smart TV", "icon": "📺", "room": "Living Room", "base": 120,
        "profile": profile([0,0,0,0,0,0,0,0.2,0.1,0,0,0.2,0.3,0.1,0,0,
                             0.3,0.5,0.8,1.0,1.0,0.9,0.4,0.1])
    },
    {
        "name": "Ceiling Fan", "icon": "🌀", "room": "Bedroom", "base": 75,
        "profile": profile([0.8,0.8,0.8,0.8,0.7,0.5,0.3,0.2,0.1,0.1,0.2,0.3,
                             0.5,0.6,0.6,0.5,0.4,0.4,0.5,0.6,0.7,0.8,0.9,0.9])
    },
    {
        "name": "LED Lights", "icon": "💡", "room": "Living Room", "base": 45,
        "profile": profile([0.3,0.1,0,0,0,0,0.2,0.4,0.3,0.1,0,0,0,0,0,0.1,
                             0.3,0.6,0.9,1.0,1.0,0.9,0.7,0.4])
    },
    {
        "name": "Washing Machine", "icon": "🧺", "room": "Utility", "base": 650,
        "profile": profile([0,0,0,0,0,0,0,0.6,0.9,0.4,0,0,0,0,0,0,0,0,
                             0.3,0,0,0,0,0])
    },
    {
        "name": "Laptop", "icon": "💻", "room": "Study", "base": 90,
        "profile": profile([0,0,0,0,0,0,0,0.3,0.6,0.8,0.9,0.9,0.5,0.7,0.9,
                             0.9,0.8,0.6,0.4,0.3,0.2,0.1,0,0])
    },
    {
        "name": "Water Heater", "icon": "🚿", "room": "Bathroom", "base": 2000,
        "profile": profile([0,0,0,0,0,0.6,1.0,0.8,0.3,0,0,0,0,0,0,0,0,
                             0.4,0.9,0.6,0.1,0,0,0])
    },
    {
        "name": "Induction Cooktop", "icon": "🍳", "room": "Kitchen", "base": 1800,
        "profile": profile([0,0,0,0,0,0,0.3,0.9,0.4,0,0,0.6,0.9,0.2,0,0,
                             0,0.3,0.9,0.7,0.1,0,0,0])
    },
]

ROOM_LIST = sorted(set(a["room"] for a in appliances))


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "sim_minutes" not in st.session_state:
    st.session_state.sim_minutes = 8 * 60  # start the simulated day at 8:00 AM

if "history" not in st.session_state:
    st.session_state.history = []

if "energy" not in st.session_state:
    st.session_state.energy = {a["name"]: 0.0 for a in appliances}

if "runtime" not in st.session_state:
    st.session_state.runtime = {a["name"]: 0.0 for a in appliances}

if "manual_override" not in st.session_state:
    st.session_state.manual_override = {a["name"]: None for a in appliances}


# ============================================================
# ADVANCE THE SIMULATED CLOCK
# ============================================================
if simulate_live:
    st.session_state.sim_minutes = (st.session_state.sim_minutes + sim_speed) % (24 * 60)

sim_hour_float = st.session_state.sim_minutes / 60.0
sim_hour_int = int(sim_hour_float) % 24
sim_time_label = f"{int(sim_hour_float)%24:02d}:{int(st.session_state.sim_minutes%60):02d}"


# ============================================================
# APPLIANCE CONTROL PANEL (manual override)
# ============================================================
st.sidebar.divider()
st.sidebar.subheader("🎛️ Manual Overrides")
for a in appliances:
    choice = st.sidebar.selectbox(
        a["name"],
        options=["Auto (profile)", "Force ON", "Force OFF"],
        key=f"override_{a['name']}"
    )
    st.session_state.manual_override[a["name"]] = (
        None if choice == "Auto (profile)" else choice == "Force ON"
    )


# ============================================================
# LIVE POWER SIMULATION — DRIVEN BY PREDEFINED PROFILES
# ============================================================
data = []

for a in appliances:
    name = a["name"]
    hour_now = a["profile"][sim_hour_int]
    hour_next = a["profile"][(sim_hour_int + 1) % 24]
    frac = sim_hour_float - int(sim_hour_float)
    interpolated = hour_now + (hour_next - hour_now) * frac  # smooth transition

    override = st.session_state.manual_override[name]
    is_on = interpolated > 0.05 if override is None else override

    if is_on:
        target_mult = interpolated if override is None else max(interpolated, 0.7)
        jitter = np.random.normal(0, 0.04) if simulate_live else 0
        power = max(5, a["base"] * max(0.05, target_mult + jitter))
    else:
        power = 0

    if is_on:
        st.session_state.runtime[name] += sim_speed / 60
        st.session_state.energy[name] += power / 1000 * (sim_speed / 60)

    data.append({
        "Appliance": name, "Icon": a["icon"], "Room": a["room"],
        "Power (W)": round(power, 1),
        "Status": "🟢 ON" if is_on else "⚪ OFF",
        "Runtime (Hours)": round(st.session_state.runtime[name], 2),
        "Energy (kWh)": round(st.session_state.energy[name], 3),
    })

df = pd.DataFrame(data)

total_power = df["Power (W)"].sum()
total_energy = sum(st.session_state.energy.values())
total_cost = total_energy * unit_rate
devices_on = (df["Power (W)"] > 0).sum()
load_pct = min(100, (total_power / 1000) / house_capacity_kw * 100)


# ============================================================
# STORE LIVE HISTORY (per appliance, for area/trend charts)
# ============================================================
snapshot = {"Time": sim_time_label, "Total Power": total_power}
for a in appliances:
    snapshot[a["name"]] = df.loc[df["Appliance"] == a["name"], "Power (W)"].values[0]
st.session_state.history.append(snapshot)

if len(st.session_state.history) > 60:
    st.session_state.history.pop(0)

history_df = pd.DataFrame(st.session_state.history)


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="main-title">🏠 HomePulse <span style="color:#4cc9f0;">⚡</span></div>
<div class="subtitle">Smart Home Energy Intelligence • Monitor • Compare • Save</div>
""", unsafe_allow_html=True)

badge_col, clock_col = st.columns([2, 1])
with badge_col:
    st.markdown('<span class="live-badge">● LIVE ENERGY MONITORING</span>',
                unsafe_allow_html=True)
with clock_col:
    st.markdown(f"🕒 Simulated house time: **{sim_time_label}**")

st.write("")


# ============================================================
# TOP METRICS + LOAD GAUGE
# ============================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">⚡ LIVE POWER</div>
        <div class="metric-value">{total_power/1000:.2f} kW</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🔋 ENERGY USED</div>
        <div class="metric-value">{total_energy:.2f} kWh</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">💰 ESTIMATED COST</div>
        <div class="metric-value">₹ {total_cost:.2f}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🟢 DEVICES RUNNING</div>
        <div class="metric-value">{devices_on} / {len(appliances)}</div>
    </div>""", unsafe_allow_html=True)

st.write("")

gauge_col, room_col = st.columns([1, 1.4])

with gauge_col:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_power / 1000,
        number={"suffix": " kW", "font": {"color": "white"}},
        title={"text": "Load vs Sanctioned Capacity", "font": {"color": "white"}},
        gauge={
            "axis": {"range": [0, house_capacity_kw], "tickcolor": "white"},
            "bar": {"color": "#4cc9f0"},
            "steps": [
                {"range": [0, house_capacity_kw * 0.6], "color": "rgba(22,199,132,0.3)"},
                {"range": [house_capacity_kw * 0.6, house_capacity_kw * 0.85], "color": "rgba(255,193,7,0.3)"},
                {"range": [house_capacity_kw * 0.85, house_capacity_kw], "color": "rgba(255,107,107,0.35)"},
            ],
        }
    ))
    fig_gauge.update_layout(template="plotly_dark", height=320,
                             margin=dict(l=20, r=20, t=50, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

with room_col:
    room_energy = df.groupby("Room")["Energy (kWh)"].sum().reset_index()
    fig_room = px.pie(room_energy, names="Room", values="Energy (kWh)", hole=0.55,
                       title="Energy Share by Room")
    fig_room.update_traces(textinfo="percent+label")
    fig_room.update_layout(template="plotly_dark", height=320,
                            margin=dict(l=20, r=20, t=50, b=10))
    st.plotly_chart(fig_room, use_container_width=True)

st.divider()


# ============================================================
# ALERTS
# ============================================================
alerts = []
if load_pct > 85:
    alerts.append("⚠️ Load is above 85% of sanctioned capacity — risk of tripping.")
high_energy = df.loc[df["Energy (kWh)"].idxmax()]
if high_energy["Energy (kWh)"] > 1.5:
    alerts.append(f"💡 {high_energy['Appliance']} has consumed over 1.5 kWh today.")
idle_running = df[(df["Appliance"].isin(["Laptop", "Smart TV"])) & (df["Power (W)"] > 0) & (sim_hour_int in [1,2,3,4])]
if not idle_running.empty:
    alerts.append("🌙 Some entertainment devices are running late at night — consider a smart plug schedule.")

if alerts:
    for al in alerts:
        st.markdown(f'<div class="alert-card">{al}</div>', unsafe_allow_html=True)
    st.write("")


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
            <div class="device-name">{row["Icon"]} {row["Appliance"]}</div>
            <p>{row["Room"]}</p>
            <div class="{status_class}">{row["Status"]}</div>
            <h3>⚡ {row["Power (W)"]:.0f} W</h3>
            ⏱️ Runtime: <b>{row["Runtime (Hours)"]:.2f} hrs</b><br>
            🔋 Energy: <b>{row["Energy (kWh)"]:.3f} kWh</b>
        </div>
        """, unsafe_allow_html=True)

st.divider()


# ============================================================
# LIVE POWER TREND + STACKED ENERGY AREA
# ============================================================
left, right = st.columns(2)

with left:
    st.subheader("📈 Live Power Trend")
    if len(history_df) > 1:
        fig_live = px.line(history_df, x="Time", y="Total Power", markers=True)
        fig_live.update_layout(template="plotly_dark", height=380,
                                margin=dict(l=20, r=20, t=30, b=20),
                                xaxis_title="Simulated Time", yaxis_title="Power (W)")
        st.plotly_chart(fig_live, use_container_width=True)

with right:
    st.subheader("📊 Appliance Power Mix Over Time")
    if len(history_df) > 1:
        appliance_names = [a["name"] for a in appliances]
        fig_area = go.Figure()
        for name in appliance_names:
            fig_area.add_trace(go.Scatter(
                x=history_df["Time"], y=history_df[name],
                mode="lines", stackgroup="one", name=name
            ))
        fig_area.update_layout(template="plotly_dark", height=380,
                                margin=dict(l=20, r=20, t=30, b=20),
                                xaxis_title="Simulated Time", yaxis_title="Power (W)",
                                legend=dict(font=dict(size=9)))
        st.plotly_chart(fig_area, use_container_width=True)

st.divider()


# ============================================================
# 24-HOUR PREDEFINED LOAD HEATMAP
# ============================================================
st.subheader("🗺️ Predefined 24-Hour Load Heatmap (Watts)")

heatmap_matrix = np.array([a["profile"] * a["base"] for a in appliances])
fig_heat = px.imshow(
    heatmap_matrix,
    labels=dict(x="Hour of Day", y="Appliance", color="Watts"),
    x=[f"{h:02d}:00" for h in range(24)],
    y=[a["name"] for a in appliances],
    color_continuous_scale="Turbo",
    aspect="auto"
)
fig_heat.add_vline(x=sim_hour_int, line_color="white", line_dash="dash")
fig_heat.update_layout(template="plotly_dark", height=420,
                        margin=dict(l=20, r=20, t=30, b=20))
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()


# ============================================================
# POWER + COST BREAKDOWN
# ============================================================
left2, right2 = st.columns(2)

with left2:
    st.subheader("🔌 Current Appliance Power Comparison")
    fig_power = px.bar(df.sort_values("Power (W)", ascending=False),
                        x="Appliance", y="Power (W)", text="Power (W)",
                        color="Room")
    fig_power.update_layout(template="plotly_dark", height=380, xaxis_tickangle=-30)
    st.plotly_chart(fig_power, use_container_width=True)

with right2:
    st.subheader("💰 Cost Contribution by Appliance")
    df["Cost (₹)"] = (df["Energy (kWh)"] * unit_rate).round(2)
    fig_cost = px.bar(df.sort_values("Cost (₹)", ascending=False),
                       x="Appliance", y="Cost (₹)", text="Cost (₹)",
                       color="Cost (₹)", color_continuous_scale="Sunsetdark")
    fig_cost.update_layout(template="plotly_dark", height=380, xaxis_tickangle=-30)
    st.plotly_chart(fig_cost, use_container_width=True)


# ============================================================
# USAGE HISTORY TABLE
# ============================================================
st.subheader("📋 Today's Appliance Usage")

usage_df = df[["Appliance", "Room", "Status", "Runtime (Hours)",
               "Energy (kWh)", "Cost (₹)"]].copy()

st.dataframe(usage_df, use_container_width=True, hide_index=True)


# ============================================================
# SMART INSIGHT
# ============================================================
highest = df.loc[df["Energy (kWh)"].idxmax()]
st.info(
    f"💡 **Smart Insight:** {highest['Appliance']} is currently your "
    f"highest energy-consuming appliance with **{highest['Energy (kWh)']:.2f} kWh** "
    f"consumed so far — driven by its predefined usage profile around {sim_time_label}."
)


# ============================================================
# AUTO REFRESH
# ============================================================
if simulate_live:
    time.sleep(2)
    st.rerun()
