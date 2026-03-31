
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import datetime
import os

st.set_page_config(layout="wide")

st.title("💼 Hydrotech Pump Engineering Tool")

# ================= UNITS =================
st.subheader("⚙️ Units")

col1, col2 = st.columns(2)

with col1:
    flow_unit = st.selectbox("Flow Unit", ["L/s", "m3/hr"])

with col2:
    head_unit = st.selectbox("Head Unit", ["m", "ft"])

def flow_to_m3hr(q):
    return q * 3.6 if flow_unit == "L/s" else q

def flow_to_ls(q):
    return q if flow_unit == "L/s" else q / 3.6

def head_to_m(h):
    return h if head_unit == "m" else h * 0.3048

# ================= MODE =================
mode = st.radio("Input Method", ["Manual (5 Points)", "Excel"])

def prepare(Q, H, P, E):
    data = sorted(zip(Q, H, P, E))
    Q, H, P, E = zip(*data)
    return np.array(Q), np.array(H), np.array(P), np.array(E)

# ================= INPUT =================
if mode == "Manual (5 Points)":
    st.subheader("Enter Curve Points")
    Q, H, P, E = [], [], [], []

    for i in range(5):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            q = st.number_input(f"Q{i+1}", key=f"q{i}")
        with c2:
            h = st.number_input(f"H{i+1}", key=f"h{i}")
        with c3:
            p = st.number_input(f"P2{i+1} (kW)", key=f"p{i}")
        with c4:
            e = st.number_input(f"Eff{i+1} (%)", key=f"e{i}")

        Q.append(flow_to_m3hr(q))
        H.append(head_to_m(h))
        P.append(p)
        E.append(e)

    Q, H, P, E = prepare(Q, H, P, E)

else:
    file = st.file_uploader("Upload Excel")

    if file:
        df = pd.read_excel(file)
        df = df.apply(pd.to_numeric, errors='coerce').dropna()

        Q = df.iloc[:,0].values
        H = df.iloc[:,1].values
        P = df.iloc[:,3].values
        E = df.iloc[:,4].values

        Q, H, P, E = prepare(Q, H, P, E)

# ================= CALC =================
if 'Q' in locals():

    st.subheader("🎯 Duty Point")

    duty_Q_input = st.number_input("Flow")
    duty_H_input = st.number_input("Head")

    duty_Q = flow_to_m3hr(duty_Q_input)
    duty_H = head_to_m(duty_H_input)

    st.subheader("⚙️ Manual Inputs")

    speed = st.number_input("Speed (rpm)", value=1450)
    motor_eff = st.number_input("Motor Efficiency (%)", value=90.0)

    cases = {
        "80%": duty_H * 0.8,
        "Duty": duty_H,
        "110%": duty_H * 1.1
    }

    results = {}

    for k, h in cases.items():
        q = np.interp(h, H[::-1], Q[::-1])
        p2 = np.interp(q, Q, P)
        eff = np.interp(q, Q, E)

        p1 = p2 / (motor_eff/100)
        overall = eff * (motor_eff/100)

        results[k] = {
            "H": h,
            "Q": flow_to_ls(q),
            "P2": p2,
            "Eff": eff,
            "Overall": overall,
            "P1": p1
        }

    st.subheader("📊 Guarantee Table")

    table = pd.DataFrame({
        "Parameter":[
            "Head",
            "Flow",
            "Speed",
            "P2 (kW)",
            "Pump Eff (%)",
            "Overall Eff (%)",
            "P1 (kW)",
            "Motor Eff (%)"
        ],
        "80%":[results["80%"]["H"],results["80%"]["Q"],speed,
               results["80%"]["P2"],results["80%"]["Eff"],
               results["80%"]["Overall"],results["80%"]["P1"],motor_eff],

        "Duty":[results["Duty"]["H"],results["Duty"]["Q"],speed,
               results["Duty"]["P2"],results["Duty"]["Eff"],
               results["Duty"]["Overall"],results["Duty"]["P1"],motor_eff],

        "110%":[results["110%"]["H"],results["110%"]["Q"],speed,
               results["110%"]["P2"],results["110%"]["Eff"],
               results["110%"]["Overall"],results["110%"]["P1"],motor_eff],
    })

    st.dataframe(table, use_container_width=True)

    # ================= PDF =================
    if st.button("📄 Generate PDF"):

        doc = SimpleDocTemplate("Pump_Report.pdf")
        styles = getSampleStyleSheet()
        elements = []

        # Logos (must exist in repo)
        if os.path.exists("logo1.png"):
            elements.append(Image("logo1.png", width=200, height=60))
        if os.path.exists("logo2.png"):
            elements.append(Image("logo2.png", width=120, height=50))

        elements.append(Spacer(1,10))

        elements.append(Paragraph("Pump Guarantee Table", styles["Title"]))
        elements.append(Spacer(1,10))

        # Table data
        pdf_data = [table.columns.tolist()] + table.values.tolist()

        pdf_table = Table(pdf_data)
        pdf_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.grey)
        ]))

        elements.append(pdf_table)

        elements.append(Spacer(1,20))

        elements.append(Paragraph(f"Date: {datetime.date.today()}", styles["Normal"]))
        elements.append(Spacer(1,20))

        elements.append(Paragraph("Hydrotech for Engineering and Technical Services", styles["Normal"]))

        doc.build(elements)

        with open("Pump_Report.pdf","rb") as f:
            st.download_button("Download PDF",f,"Pump_Report.pdf")
