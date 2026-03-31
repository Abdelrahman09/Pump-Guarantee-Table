
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("🔥 Pump Tool ULTIMATE v3")

file = st.file_uploader("Upload Flygt Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df_numeric = df.apply(pd.to_numeric, errors='coerce')
    df_clean = df_numeric.dropna()

    Q = df_clean.iloc[:, 0].values  # m3/hr
    H = df_clean.iloc[:, 1].values
    P2 = df_clean.iloc[:, 3].values  # shaft power (kW)
    Eff_pump = df_clean.iloc[:, 4].values  # pump efficiency %

    data = sorted(zip(Q, H, P2, Eff_pump))
    Q, H, P2, Eff_pump = zip(*data)
    Q, H, P2, Eff_pump = map(np.array, (Q, H, P2, Eff_pump))

    st.subheader("🎯 Enter Duty Point")
    duty_Q = st.number_input("Duty Flow (m3/hr)", value=50.0)
    duty_H = st.number_input("Duty Head (m)", value=20.0)

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
        p2 = np.interp(flow, Q, P2)
        eff_p = np.interp(flow, Q, Eff_pump)

        p1 = p2 / (motor_eff/100)  # input power
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

    st.subheader("📊 Results Table")

    table = pd.DataFrame({
        "Parameter": [
            "Head (m)",
            "Flow rate (L/s)",
            "Speed (rpm)",
            "Water horse power P2 (kW)",
            "Manometric efficiency (%)",
            "Overall efficiency (%)",
            "Power absorbed P1 (kW)",
            "Motor efficiency (%)"
        ],
        "80%": [
            results["80%"]["H"],
            results["80%"]["Q_ls"],
            results["80%"]["Speed"],
            results["80%"]["P2"],
            results["80%"]["Eff_p"],
            results["80%"]["Overall"],
            results["80%"]["P1"],
            results["80%"]["MotorEff"]
        ],
        "Duty": [
            results["Duty"]["H"],
            results["Duty"]["Q_ls"],
            results["Duty"]["Speed"],
            results["Duty"]["P2"],
            results["Duty"]["Eff_p"],
            results["Duty"]["Overall"],
            results["Duty"]["P1"],
            results["Duty"]["MotorEff"]
        ],
        "110%": [
            results["110%"]["H"],
            results["110%"]["Q_ls"],
            results["110%"]["Speed"],
            results["110%"]["P2"],
            results["110%"]["Eff_p"],
            results["110%"]["Overall"],
            results["110%"]["P1"],
            results["110%"]["MotorEff"]
        ]
    })

    st.dataframe(table)

    fig, ax = plt.subplots()
    ax.plot(Q, H, label="Pump Curve")
    ax.scatter(duty_Q, duty_H, color='red', label="Duty Point")
    ax.set_xlabel("Flow (m3/hr)")
    ax.set_ylabel("Head (m)")
    ax.legend()
    st.pyplot(fig)

    csv = table.to_csv(index=False)
    st.download_button("📥 Download Report (CSV)", csv, "report.csv")
