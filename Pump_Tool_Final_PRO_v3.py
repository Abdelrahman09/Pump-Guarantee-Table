
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import datetime
import os

st.set_page_config(layout="wide")

st.title("💼 Hydrotech Pump Engineering Tool")

# ===== Helper for rounding =====
def r(x):
    return round(float(x), 2)

# ===== Units =====
flow_unit = st.selectbox("Flow Unit", ["L/s", "m3/hr"])
head_unit = st.selectbox("Head Unit", ["m", "ft"])

def flow_to_m3hr(q):
    return q * 3.6 if flow_unit == "L/s" else q

def flow_to_ls(q):
    return q if flow_unit == "L/s" else q / 3.6

def head_to_m(h):
    return h if head_unit == "m" else h * 0.3048

# ===== Model input =====
model_name = st.text_input("Pump Model", value="Enter Model")

# ===== Input Mode =====
mode = st.radio("Input Method", ["Manual (5 Points)", "Excel"])

def prepare(Q, H, P, E):
    data = sorted(zip(Q, H, P, E))
    Q, H, P, E = zip(*data)
    return np.array(Q), np.array(H), np.array(P), np.array(E)

# ===== Input =====
if mode == "Manual (5 Points)":
    Q, H, P, E = [], [], [], []
    for i in range(5):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            q = st.number_input(f"Q{i+1}", key=f"q{i}")
        with c2:
            h = st.number_input(f"H{i+1}", key=f"h{i}")
        with c3:
            p = st.number_input(f"P2{i+1}", key=f"p{i}")
        with c4:
            e = st.number_input(f"Eff{i+1}", key=f"e{i}")

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

# ===== Calculation =====
if 'Q' in locals():

    duty_Q_input = st.number_input("Duty Flow")
    duty_H_input = st.number_input("Duty Head")

    duty_Q = flow_to_m3hr(duty_Q_input)
    duty_H = head_to_m(duty_H_input)

    speed = st.number_input("Speed (rpm)", value=1450)
    motor_eff = st.number_input("Motor Efficiency (%)", value=90.0)

    cases = {"80%": duty_H*0.8, "Duty": duty_H, "110%": duty_H*1.1}
    results = {}

    for k, h in cases.items():
        q = np.interp(h, H[::-1], Q[::-1])
        p2 = np.interp(q, Q, P)
        eff = np.interp(q, Q, E)
        p1 = p2/(motor_eff/100)
        overall = eff*(motor_eff/100)

        results[k] = {
            "H": r(h), "Q": r(flow_to_ls(q)),
            "P2": r(p2), "Eff": r(eff),
            "Overall": r(overall), "P1": r(p1)
        }

    table = pd.DataFrame({
        "Parameter":["Head","Flow","Speed","P2","Pump Eff","Overall Eff","P1","Motor Eff"],
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

    st.dataframe(table)

    # ===== PDF =====
    if st.button("Generate PDF"):

        doc = SimpleDocTemplate("Pump_Report.pdf", pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Header logos
        header_data = []
        left_logo = "logo1.png" if os.path.exists("logo1.png") else ""
        right_logo = "logo2.png" if os.path.exists("logo2.png") else ""

        header_row = []
        header_row.append(Image(left_logo, width=150, height=50) if left_logo else "")
        header_row.append("")
        header_row.append(Image(right_logo, width=120, height=40) if right_logo else "")

        header_data.append(header_row)

        header_table = Table(header_data, colWidths=[200,150,200])
        elements.append(header_table)
        elements.append(Spacer(1,10))

        # Title
        elements.append(Paragraph("Pump Performance Guarantee", styles["Title"]))
        elements.append(Spacer(1,10))

        # Info block
        info = f"""
        Make: Flygt<br/>
        Origin: Sweden<br/>
        Model: {model_name}<br/>
        Date: {datetime.date.today()}
        """
        elements.append(Paragraph(info, styles["Normal"]))
        elements.append(Spacer(1,10))

        # Table
        pdf_data = [table.columns.tolist()] + table.values.tolist()

        pdf_table = Table(pdf_data)
        pdf_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BOX', (0,0), (-1,-1), 2, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.grey)
        ]))

        elements.append(pdf_table)
        elements.append(Spacer(1,20))

        # Signature
        elements.append(Paragraph("Hydrotech for Engineering and Technical Services", styles["Normal"]))

        doc.build(elements)

        with open("Pump_Report.pdf","rb") as f:
            st.download_button("Download PDF",f,"Pump_Report.pdf")
