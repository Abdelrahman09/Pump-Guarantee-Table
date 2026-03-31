
import streamlit as st
import pandas as pd
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import datetime
import os

st.set_page_config(layout="wide")

st.title("💼 Hydrotech Pump Engineering Tool")

def r(x): return round(float(x), 2)

flow_unit = st.selectbox("Flow Unit", ["L/s", "m3/hr"])
head_unit = st.selectbox("Head Unit", ["m", "ft"])

def flow_to_m3hr(q): return q * 3.6 if flow_unit == "L/s" else q
def flow_to_ls(q): return q if flow_unit == "L/s" else q / 3.6
def head_to_m(h): return h if head_unit == "m" else h * 0.3048

model_name = st.text_input("Pump Model", value="")

mode = st.radio("Input Method", ["Manual (5 Points)", "Excel"])

def prepare(Q,H,P,E):
    data = sorted(zip(Q,H,P,E))
    Q,H,P,E = zip(*data)
    return map(np.array,(Q,H,P,E))

if mode == "Manual (5 Points)":
    Q,H,P,E=[],[],[],[]
    for i in range(5):
        c1,c2,c3,c4=st.columns(4)
        with c1: q=st.number_input(f"Q{i}",key=f"q{i}")
        with c2: h=st.number_input(f"H{i}",key=f"h{i}")
        with c3: p=st.number_input(f"P2{i}",key=f"p{i}")
        with c4: e=st.number_input(f"Eff{i}",key=f"e{i}")
        Q.append(flow_to_m3hr(q)); H.append(head_to_m(h)); P.append(p); E.append(e)
    Q,H,P,E=prepare(Q,H,P,E)

else:
    file=st.file_uploader("Upload Excel")
    if file:
        df=pd.read_excel(file).apply(pd.to_numeric,errors='coerce').dropna()
        Q=df.iloc[:,0].values; H=df.iloc[:,1].values
        P=df.iloc[:,3].values; E=df.iloc[:,4].values
        Q,H,P,E=prepare(Q,H,P,E)

if 'Q' in locals():

    duty_Q=flow_to_m3hr(st.number_input("Flow"))
    duty_H=head_to_m(st.number_input("Head"))

    speed=st.number_input("Speed",value=1450)
    motor_eff=st.number_input("Motor Eff",value=90.0)

    cases={"80%":duty_H*0.8,"Duty":duty_H,"110%":duty_H*1.1}
    results={}

    for k,h in cases.items():
        q=np.interp(h,H[::-1],Q[::-1])
        p2=np.interp(q,Q,P)
        eff=np.interp(q,Q,E)
        p1=p2/(motor_eff/100)
        overall=eff*(motor_eff/100)
        results[k]={"H":r(h),"Q":r(flow_to_ls(q)),"P2":r(p2),
                    "Eff":r(eff),"Overall":r(overall),"P1":r(p1)}

    table=pd.DataFrame({
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

    st.dataframe(table,use_container_width=True)

    if st.button("Generate PDF"):

        def draw_border(canvas,doc):
            canvas.setLineWidth(2)
            canvas.rect(20,20,555,800)

        doc=SimpleDocTemplate("Pump_Report.pdf",pagesize=A4)
        styles=getSampleStyleSheet()
        elements=[]

        # HEADER
        left = Image("logo1.png", width=220, height=70) if os.path.exists("logo1.png") else ""
        right = Image("logo2.png", width=180, height=60) if os.path.exists("logo2.png") else ""

        header=Table([[left,"",right]],colWidths=[200,150,200])
        elements.append(header)
        elements.append(Spacer(1,15))

        elements.append(Paragraph("<b>Pump Performance Guarantee</b>",styles["Title"]))
        elements.append(Spacer(1,10))

        info=f"Make: Flygt<br/>Origin: Sweden<br/>Model: {model_name}<br/>Date: {datetime.date.today()}"
        elements.append(Paragraph(info,styles["Normal"]))
        elements.append(Spacer(1,15))

        # TABLE BIGGER
        data=[table.columns.tolist()]+table.values.tolist()

        pdf_table=Table(data,colWidths=[120,120,120,120])
        pdf_table.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),1,colors.black),
            ('BOX',(0,0),(-1,-1),2,colors.black),
            ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
            ('FONTSIZE',(0,0),(-1,-1),10),
            ('ALIGN',(0,0),(-1,-1),'CENTER')
        ]))

        elements.append(pdf_table)
        elements.append(Spacer(1,30))

        elements.append(Paragraph("Hydrotech for Engineering and Technical Services",styles["Normal"]))

        doc.build(elements,onFirstPage=draw_border,onLaterPages=draw_border)

        with open("Pump_Report.pdf","rb") as f:
            st.download_button("Download PDF",f,"Pump_Report.pdf")
