import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image, ImageOps, ImageEnhance
import re

# --- 1. SETTINGS ---
st.set_page_config(page_title="PhD Multi-Spec Dashboard", layout="wide")
st.title("🔬 Integrated IR, H-NMR & C-NMR Interpretation Suite")
st.markdown("Automated Peak Detection (IR) + Manual Correlation (NMR) based on Table 2.3")

# --- 2. MASTER DATABASES (FROM YOUR CHARTS) ---

IR_DB = {
    "Alkane C-H": [2850, 2970], "Alkene =C-H": [3010, 3100],
    "Aromatic C-H": [3000, 3100], "Alkyne ≡C-H": [3260, 3330],
    "Aldehyde C-H (Fermi)": [2700, 2850], "Alcohol/Phenol O-H": [3200, 3650],
    "Carboxylic Acid O-H": [2500, 3300], "Nitrile (C≡N)": [2210, 2260],
    "Ester (C=O)": [1735, 1750], "Aldehyde (C=O)": [1720, 1740],
    "Ketone (C=O)": [1705, 1725], "Carboxylic Acid (C=O)": [1700, 1720],
    "Amide (C=O)": [1630, 1690], "Nitro (-NO2)": [1330, 1550]
}

H_NMR_DB = {
    "R-CH3 (Methyl)": [0.8, 1.0], "R-CH2-R (Methylene)": [1.2, 1.4],
    "R-CH-R (Methine)": [1.4, 1.7], "C=C-CH (Allylic)": [1.6, 2.6],
    "R-C≡CH (Alkyne)": [2.0, 3.0], "RO2C-CH (Ester alpha)": [2.0, 2.2],
    "O=C-CH (Ketone alpha)": [2.0, 2.7], "ROH (Alcohol)": [2.0, 4.0],
    "ArOH (Phenol)": [4.0, 8.0], "Ar-CH (Benzylic)": [2.2, 3.0],
    "Halide-CH (I/Br/Cl)": [2.0, 4.0], "HO-CH (Alcohol alpha)": [3.4, 4.0],
    "RO-CH (Ether alpha)": [3.3, 4.0], "F-CH (Fluoride)": [4.0, 4.5],
    "R-C=CH (Vinyl)": [4.6, 5.9], "Aromatic (Ar-H)": [6.0, 8.5],
    "Aldehyde (O=C-H)": [9.0, 10.0], "Carboxylic Acid (RCO2H)": [10.0, 13.0]
}

C_NMR_DB = {
    "Primary Alkyl (R-CH3)": [8, 35], "Secondary Alkyl (R2CH2)": [15, 50],
    "Tertiary Alkyl (R3CH)": [20, 60], "Alkyne (C≡C)": [65, 85],
    "Alkene (C=C)": [100, 150], "Aromatic Ring (C)": [110, 170],
    "C-Halogen (I/Br/Cl)": [0, 80], "C-O (Alcohol/Ether)": [50, 80],
    "Amide/Ester (C=O)": [165, 175], "Carboxylic Acid (C=O)": [175, 185],
    "Aldehyde (C=O)": [190, 200], "Ketone (C=O)": [205, 220]
}

# --- 3. TABBED INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📡 Infrared (IR)", "🧬 H-NMR", "💎 13C-NMR"])

# --- TAB 1: IR ANALYSIS ---
with tab1:
    st.header("IR Spectrum Image Analysis")
    f1 = st.file_uploader("Upload IR Graph", type=['png', 'jpg', 'jpeg'], key="ir")
    if f1:
        img = Image.open(f1)
        st.image(img, use_container_width=True)
        if st.button("🚀 Extract IR Data"):
            with st.spinner("Running OCR..."):
                reader = easyocr.Reader(['en'])
                res = reader.readtext(np.array(img), rotation_info=[90, 270])
                ir_peaks = []
                for x in res:
                    clean = "".join(re.findall(r'[0-9.]+', x[1].replace("I","1")))
                    try:
                        v = float(clean)
                        if 400 <= v <= 4000:
                            for grp, r in IR_DB.items():
                                if (r[0]-15) <= v <= (r[1]+15):
                                    ir_peaks.append({"Peak": v, "Group": grp})
                    except: continue
                if ir_peaks:
                    st.table(pd.DataFrame(ir_peaks).drop_duplicates(subset=["Peak"]))
                else: st.error("No peaks detected.")

# --- TAB 2: H-NMR ANALYSIS ---
with tab2:
    st.header("H-NMR Correlation (Chart 2)")
    h_in = st.text_input("Enter H-NMR shifts (δ) e.g., 1.3, 7.5, 9.8", key="hin")
    hz_in = st.number_input("Enter Coupling Constant (J in Hz) if applicable", 0.0, 20.0, 0.0)
    
    if h_in:
        h_shifts = [float(x.strip()) for x in h_in.split(",") if x.strip()]
        h_results = []
        for s in h_shifts:
            match = "Unknown"
            for label, r in H_NMR_DB.items():
                if r[0] <= s <= r[1]: match = label
            h_results.append({"Shift (δ)": s, "Interpretation": match})
        st.table(pd.DataFrame(h_results))
        
        if hz_in > 0:
            if 12 <= hz_in <= 18: st.info(f"✅ J={hz_in} Hz suggests **Trans-Alkene** geometry.")
            elif 6 <= hz_in <= 12: st.info(f"✅ J={hz_in} Hz suggests **Cis-Alkene** geometry.")

# --- TAB 3: 13C-NMR ANALYSIS ---
with tab3:
    st.header("13C-NMR Correlation (Chart 1)")
    c_in = st.text_input("Enter C-NMR shifts (δ) e.g., 25.1, 128.4, 195.0", key="cin")
    if c_in:
        c_shifts = [float(x.strip()) for x in c_in.split(",") if x.strip()]
        c_results = []
        for s in c_shifts:
            match = "Other"
            for label, r in C_NMR_DB.items():
                if r[0] <= s <= r[1]: match = label
            c_results.append({"Shift (δ)": s, "Carbon Type": match})
        st.table(pd.DataFrame(c_results))

# --- 4. GLOBAL CONCLUSION ---
if h_in and c_in:
    st.divider()
    st.subheader("🏁 Multi-Spectral Structural Conclusion")
    h_val = [float(x.strip()) for x in h_in.split(",") if x.strip()]
    c_val = [float(x.strip()) for x in c_in.split(",") if x.strip()]
    
    if any(9<=s<=10 for s in h_val) and any(190<=s<=200 for s in c_val):
        st.success("🎯 **Conclusion: ALDEHYDE confirmed by H-NMR and C-NMR.**")
    elif any(10<=s<=13 for s in h_val) and any(175<=s<=185 for s in c_val):
        st.success("🎯 **Conclusion: CARBOXYLIC ACID confirmed by H-NMR and C-NMR.**")
