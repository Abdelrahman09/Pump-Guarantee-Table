
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pump Tool Hybrid", layout="wide")

st.title("🔥 Pump Tool - Excel + Manual Curve Mode")

mode = st.radio("Select Input Method:", ["Excel Upload", "Manual Input (5 Points)"])

def prepare_arrays(Q, H, P, Eff):
    data = sorted(zip(Q, H, P, Eff))
    Q, H, P, Eff = zip(*data)
    return np.array(Q), np.array(H), np.array(P), np.array(Eff)

# ================== EXCEL MODE ==================
if mode == "Excel Upload":
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        df_clean = df_numeric.dropna()

        Q = df_clean.iloc[:, 0].values
        H = df_clean.iloc[:, 1].values
        P = df_clean.iloc[:, 3].values
        Eff = df_clean.iloc[:, 4].values

        Q, H, P, Eff = prepare_arrays(Q, H, P, Eff)

# ================== MANUAL MODE ==================
else:
    st.subheader("Enter 5 Curve Points")

    Q, H, P, Eff = [], [], [], []

    for i in range(5):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            q = st.number_input(f"Q{i+1} (L/s)", key=f"q{i}")
        with col2:
            h = st.number_input(f"H{i+1} (m)", key=f"h{i}")
        with col3:
            p = st.number_input(f"P{i+1} (kW)", key=f"p{i}")
        with col4:
            e = st.number_input(f"Eff{i+1} (%)", key=f"e{i}")

        Q.append(q * 3.6)
        H.append(h)
        P.append(p)
        Eff.append(e)

    Q, H, P, Eff = prepare_arrays(Q, H, P, Eff)

# ================== CALCULATION ==================
if 'Q' in locals() and len(Q) > 0:

    st.subheader("🎯 Duty Point")
    duty_Q = st.number_input("Flow (m3/hr)", value=float(np.mean(Q)))
    duty_H = st.number_input("Head (m)", value=float(np.mean(H)))

    st.subheader("⚙️ Manual Inputs")
    speed = st.number_input("Speed (rpm)", value=1450)
    motor_eff = st.number_input("Motor Efficiency (%)", value=90.0)

    def m3hr_to_ls(q):
        return q / 3.6

    cases = {
        "80%": duty_H * 0.8,
        "Duty": duty_H,
        "110%": duty_H * 1.1
    }

    results = {}

    for name, head in cases.items():
        flow = np.interp(head, H[::-1], Q[::-1])
        p2 = np.interp(flow, Q, P)
        eff_p = np.interp(flow, Q, Eff)

        p1 = p2 / (motor_eff/100)
        overall_eff = eff_p * (motor_eff/100)

        results[name] = {
            "H": head,
            "Q_ls": m3hr_to_ls(flow),
            "Speed": speed,
            "P2": p2,
            "Eff_p": eff_p,
            "Overall": overall_eff,
            "P1": p1,
            "MotorEff": motor_eff
        }

    st.subheader("📊 Guarantee Table")

    table = pd.DataFrame({
        "Parameter": [
            "Head (m)",
            "Flow rate (L/s)",
            "Speed (rpm)",
            "Water HP P2 (kW)",
            "Pump Efficiency (%)",
            "Overall Efficiency (%)",
            "Input Power P1 (kW)",
            "Motor Efficiency (%)"
        ],
        "80%": [results["80%"][k] for k in ["H","Q_ls","Speed","P2","Eff_p","Overall","P1","MotorEff"]],
        "Duty": [results["Duty"][k] for k in ["H","Q_ls","Speed","P2","Eff_p","Overall","P1","MotorEff"]],
        "110%": [results["110%"][k] for k in ["H","Q_ls","Speed","P2","Eff_p","Overall","P1","MotorEff"]],
    })

    st.dataframe(table, use_container_width=True)

    fig, ax = plt.subplots()
    ax.plot(Q, H, label="Pump Curve")
    ax.scatter(duty_Q, duty_H, color='red', label="Duty Point")
    ax.set_xlabel("Flow (m3/hr)")
    ax.set_ylabel("Head (m)")
    ax.legend()
    ax.grid()
    st.pyplot(fig)

    csv = table.to_csv(index=False)
    st.download_button("📥 Download Report", csv, "report.csv")
