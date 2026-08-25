import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Smart NIALM Energy Monitor",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Smart NIALM Energy Disaggregation Dashboard")
st.caption("Edge-disaggregated telemetry from main service panel (ESP32 + CT / ZMPT101B)")

# Sidebar Settings
st.sidebar.header("⚙️ Configuration")
unit_rate = st.sidebar.number_input("Electricity Tariff (₹/kWh)", min_value=1.0, max_value=20.0, value=7.5, step=0.5)
sim_live = st.sidebar.toggle("Simulate Live Feed", value=True)

# Generate synthetic disaggregated data
np.random.seed(42)
appliances = ["Refrigerator (Compressor)", "Inverter AC", "Induction Cooktop", "Water Heater", "Vampire / Standby"]
p_values = [140 + np.random.normal(0, 5), 1250 + np.random.normal(0, 30), 0, 1800, 35 + np.random.normal(0, 2)]
q_values = [80, 210, 0, 10, 15]

df_appliances = pd.DataFrame({
    "Appliance": appliances,
    "Active Power (W)": [max(0, p) for p in p_values],
    "Reactive Power (VAR)": [max(0, q) for q in q_values],
    "Status": ["Running", "Running", "Idle", "Active (Peak)", "Always On"],
    "Health": ["Normal", "Harmonic Warning ⚠️", "Normal", "Normal", "Normal"]
})

total_p = df_appliances["Active Power (W)"].sum()
est_daily_cost = (total_p * 24 / 1000) * unit_rate

# Top Key Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Active Load (P)", f"{total_p:.1f} W", "+120 W transient")
col2.metric("Grid Voltage (RMS)", "231.4 V", "-1.2 V")
col3.metric("Projected Daily Cost", f"₹ {est_daily_cost:.2f}")
col4.metric("Active Anomaly Alerts", "1 Warning", delta_color="inverse")

st.divider()

# Main Visualizations
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📊 Disaggregated Real-Time Load")
    fig_pie = px.pie(
        df_appliances[df_appliances["Active Power (W)"] > 0],
        values="Active Power (W)",
        names="Appliance",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("📈 P-Q Feature Space Breakdown")
    fig_bar = go.Figure(data=[
        go.Bar(name='Active Power (P [W])', x=df_appliances["Appliance"], y=df_appliances["Active Power (W)"]),
        go.Bar(name='Reactive Power (Q [VAR])', x=df_appliances["Appliance"], y=df_appliances["Reactive Power (VAR)"])
    ])
    fig_bar.update_layout(barmode='group', xaxis_tickangle=-25)
    st.plotly_chart(fig_bar, use_container_width=True)

# Predictive Diagnostics Table
st.subheader("🛠️ Appliance Telemetry & Diagnostics")
st.dataframe(
    df_appliances,
    use_container_width=True,
    column_config={
        "Active Power (W)": st.column_config.ProgressColumn(
            "Active Power", min_value=0, max_value=2500, format="%d W"
        ),
    },
    hide_index=True
)

# Maintenance Warning Callout
st.warning(
    "**Predictive Alert — Inverter AC:** High-frequency harmonic distortion detected (THD > 8.2%). "
    "Signifies potential compressor bearing wear or capacitor aging.",
    icon="⚠️"
)
