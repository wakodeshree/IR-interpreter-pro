import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image, ImageOps, ImageEnhance
import re

# --- 1. SETTINGS & PAGE CONFIG ---
st.set_page_config(page_title="PhD Multi-Spec Dashboard", layout="wide")
st.title("🔬 Integrated IR / H-NMR / C-NMR Graph Interpreter")
st.markdown("Automated Peak Detection for all Spectral Graphs")

# --- 2. MASTER DATABASES (FROM YOUR CHARTS) ---

IR_DB = {
    "Alkane C-H": [2850, 2970], "Aldehyde C-H (Fermi)": [2700, 2850],
    "Ester (C=O)": [1735, 1750], "Aldehyde (C=O)": [1720, 1740],
    "Ketone (C=O)": [1705, 1725], "Carboxylic Acid (C=O)": [1700, 1720],
    "Alcohol/Phenol O-H": [3200, 3650], "Nitro (-NO2)": [1330, 1550]
}

H_NMR_DB = {
    "R-CH3/CH2 (Aliphatic)": [0.8, 1.7], "Allylic/Ketone alpha": [1.6, 2.7],
    "Benzylic (Ar-CH)": [2.2, 3.0], "Halide-CH (I/Br/Cl)": [2.0, 4.5],
    "Alcohol/Ether alpha": [3.3, 4.0], "Vinyl (R-C=CH)": [4.6, 5.9],
    "Aromatic (Ar-H)": [6.0, 8.5], "Aldehyde (CHO)": [9.0, 10.0],
    "Acid (RCO2H)": [10.0, 13.0]
}

C_NMR_DB = {
    "Alkyl (CH3/CH2/CH)": [8, 60], "Alkyne (C≡C)": [65, 85],
    "Alkene (C=C)": [100, 150], "Aromatic (C)": [110, 170],
    "C-Halogen/C-O": [25, 80], "Amide/Ester (C=O)": [165, 175],
    "Acid (C=O)": [175, 185], "Aldehyde (C=O)": [190, 200],
    "Ketone (C=O)": [205, 220]
}

# --- 3. TABBED INTERFACE ---
t1, t2, t3 = st.tabs(["📡 Infrared (IR)", "🧬 H-NMR", "💎 13C-NMR"])

# --- TAB 1: IR ANALYSIS (Vertical Labels) ---
with t1:
    st.header("IR Image Analysis")
    f1 = st.file_uploader("Upload IR Graph", type=['png', 'jpg', 'jpeg'], key="ir")
    if f1:
        img1 = Image.open(f1)
        st.image(img1, use_container_width=True)
        if st.button("Analyze IR"):
            with st.spinner("OCR Processing..."):
                reader = easyocr.Reader(['en'])
                res = reader.readtext(np.array(img1), rotation_info=[90, 270])
                ir_results = []
                for x in res:
                    clean = "".join(re.findall(r'[0-9.]+', x[1].replace("I","1")))
                    try:
                        v = float(clean)
                        if 400 <= v <= 4000:
                            for grp, r in IR_DB.items():
                                if (r[0]-10) <= v <= (r[1]+10):
                                    ir_results.append({"Peak": v, "Interpretation": grp})
                    except: continue
                if ir_results:
                    st.table(pd.DataFrame(ir_results).drop_duplicates(subset=["Peak"]))
                else: st.error("No IR peaks detected.")

# --- TAB 2: H-NMR ANALYSIS (Horizontal Labels) ---
with t2:
    st.header("H-NMR Image Analysis")
    f2 = st.file_uploader("Upload H-NMR Graph", type=['png', 'jpg', 'jpeg'], key="h")
    if f2:
        img2 = Image.open(f2)
        st.image(img2, use_container_width=True)
        if st.button("Analyze H-NMR"):
            with st.spinner("OCR Processing..."):
                reader = easyocr.Reader(['en'])
                # No rotation_info needed for horizontal NMR axes
                res2 = reader.readtext(np.array(img2))
                h_results = []
                for x in res2:
                    clean = "".join(re.findall(r'[0-9.]+', x[1].replace("I","1")))
                    try:
                        v = float(clean)
                        if 0 <= v <= 15: # H-NMR Range
                            for grp, r in H_NMR_DB.items():
                                if r[0] <= v <= r[1]:
                                    h_results.append({"Shift (δ)": v, "Proton Type": grp})
                    except: continue
                if h_results:
                    st.table(pd.DataFrame(h_results).drop_duplicates())
                else: st.error("No ppm values detected.")

# --- TAB 3: C-NMR ANALYSIS (Horizontal Labels) ---
with t3:
    st.header("13C-NMR Image Analysis")
    f3 = st.file_uploader("Upload C-NMR Graph", type=['png', 'jpg', 'jpeg'], key="c")
    if f3:
        img3 = Image.open(f3)
        st.image(img3, use_container_width=True)
        if st.button("Analyze C-NMR"):
            with st.spinner("OCR Processing..."):
                reader = easyocr.Reader(['en'])
                res3 = reader.readtext(np.array(img3))
                c_results = []
                for x in res3:
                    clean = "".join(re.findall(r'[0-9.]+', x[1].replace("I","1")))
                    try:
                        v = float(clean)
                        if 0 <= v <= 230: # C-NMR Range
                            for grp, r in C_NMR_DB.items():
                                if r[0] <= v <= r[1]:
                                    c_results.append({"Shift (δ)": v, "Carbon Type": grp})
                    except: continue
                if c_results:
                    st.table(pd.DataFrame(c_results).drop_duplicates())
                else: st.error("No Carbon shifts detected.")
