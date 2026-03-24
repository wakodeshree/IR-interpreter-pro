import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE ULTIMATE MASTER DATABASES (EXACTLY FROM YOUR CHARTS) ---

IR_DB = {
    "Alcohol O-H (Broad)": [3200, 3650], "Carboxylic Acid O-H": [2400, 3400],
    "Amine/Amide N-H": [3100, 3500], "Alkyne ≡C-H": [3250, 3350],
    "Aromatic/Alkene C-H": [3000, 3100], "Alkane C-H": [2850, 2970],
    "Aldehyde C-H (Fermi)": [2720, 2850], "Nitrile C≡N": [2240, 2260],
    "Alkyne C≡C": [2100, 2250], "Anhydride/Acid Chloride": [1760, 1810],
    "Ester C=O": [1730, 1750], "Aldehyde C=O": [1720, 1740],
    "Ketone C=O": [1705, 1725], "Carboxylic Acid C=O": [1700, 1725],
    "Amide C=O": [1630, 1680], "Alkene C=C": [1600, 1680],
    "Aromatic C=C": [1475, 1600], "Nitro (-NO2)": [1350, 1550],
    "C-O Stretch": [1000, 1300], "C-Cl (Halide)": [540, 785]
}

H_NMR_DB = {
    "R-CH3 (Methyl)": [0.8, 1.0], "R-CH2-R (Methylene)": [1.2, 1.4],
    "R-CH-R (Methine)": [1.4, 1.7], "Allylic (C=C-CH)": [1.6, 2.6],
    "Alkyne (R-C≡CH)": [2.0, 3.0], "Ester alpha (RO2C-CH)": [2.0, 2.2],
    "Ketone alpha (O=C-CH)": [2.0, 2.7], "Alcohol (ROH)": [2.0, 4.0],
    "Amine (RNH2)": [2.0, 4.0], "Benzylic (Ar-CH)": [2.2, 3.0],
    "Iodide (I-CH)": [2.0, 4.0], "Bromide (Br-CH)": [2.5, 4.0],
    "Chloride (Cl-CH)": [3.0, 4.0], "Ether alpha (RO-CH)": [3.3, 4.0],
    "Alcohol alpha (HO-CH)": [3.4, 4.0], "Fluoride (F-CH)": [4.0, 4.5],
    "Vinyl (R-C=CH)": [4.6, 5.9], "Aromatic (Ar-H)": [6.0, 8.5],
    "Aldehyde (CHO)": [9.0, 10.0], "Carboxylic Acid (RCO2H)": [10.0, 13.0]
}

C_NMR_DB = {
    "Primary Alkyl (R-CH3)": [8, 35], "Secondary Alkyl (R2CH2)": [15, 50],
    "Tertiary Alkyl (R3CH)": [20, 60], "Quaternary Alkyl (R4C)": [30, 40],
    "Alkyne (C≡C)": [65, 85], "Alkene (C=C)": [100, 150],
    "Aromatic Ring (C)": [110, 170], "C-I (Iodide)": [0, 40],
    "C-Br (Bromide)": [25, 65], "C-Cl (Chloride)": [35, 80],
    "C-N (Amine)": [40, 60], "C-O (Alcohol/Ether)": [50, 80],
    "Amide/Ester (C=O)": [165, 175], "Carboxylic Acid (C=O)": [175, 185],
    "Aldehyde (C=O)": [190, 200], "Ketone (C=O)": [205, 220]
}

# --- 2. CORE PROCESSING ENGINE ---

def process_spectrum(image, mode="IR"):
    reader = easyocr.Reader(['en'])
    # IR has vertical labels; NMR axes are horizontal
    rot = [90, 270] if mode == "IR" else None
    results = reader.readtext(np.array(image), rotation_info=rot)
    
    # Numbers to ignore (Scale markers)
    ignore_list = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500, 200, 150, 100, 50, 0]
    
    final_output = []
    for (bbox, text, prob) in results:
        # Clean string to keep only decimals and numbers
        clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
        if not clean or len(clean) < 2: continue
        
        try:
            val = float(clean)
            # Filter Scale: Ignore round integers < 15 in NMR or round integers in IR
            if int(val) in ignore_list: continue
            if mode == "H-NMR" and val.is_integer() and val <= 13: continue

            # Database Matching
            db = IR_DB if mode == "IR" else (H_NMR_DB if mode == "H-NMR" else C_NMR_DB)
            for group, r in db.items():
                # Allow a small buffer for experimental deviation
                buffer = 15 if mode == "IR" else 0.1
                if r[0]-buffer <= val <= r[1]+buffer:
                    final_output.append({"Peak/Shift": val, "Interpretation": group})
        except: continue
    
    return pd.DataFrame(final_output).drop_duplicates(subset=["Peak/Shift"]).sort_values("Peak/Shift", ascending=False)

# --- 3. DASHBOARD INTERFACE ---

st.set_page_config(page_title="PhD Multi-Spec Suite", layout="wide")
st.title("🔬 Integrated PhD Multi-Spectral Suite")
st.markdown("Advanced Peak Detection & Interpretation (IR, H-NMR, 13C-NMR)")

t1, t2, t3 = st.tabs(["📡 IR Analysis", "🧬 H-NMR Analysis", "💎 13C-NMR Analysis"])

with t1:
    st.header("Infrared (IR) Image Analysis")
    f1 = st.file_uploader("Upload IR Graph", type=['png', 'jpg', 'jpeg'], key="ir")
    if f1 and st.button("🚀 Analyze IR Graph"):
        df = process_spectrum(Image.open(f1), mode="IR")
        if not df.empty: st.table(df)
        else: st.warning("No IR peaks detected. Check image quality.")

with t2:
    st.header("Proton (H-NMR) Image Analysis")
    f2 = st.file_uploader("Upload H-NMR Graph", type=['png', 'jpg', 'jpeg'], key="h")
    if f2 and st.button("🚀 Analyze H-NMR Graph"):
        df = process_spectrum(Image.open(f2), mode="H-NMR")
        if not df.empty: st.table(df)
        else: st.warning("No H-NMR signals detected.")

with t3:
    st.header("Carbon (13C-NMR) Image Analysis")
    f3 = st.file_uploader("Upload C-NMR Graph", type=['png', 'jpg', 'jpeg'], key="c")
    if f3 and st.button("🚀 Analyze 13C-NMR Graph"):
        df = process_spectrum(Image.open(f3), mode="C-NMR")
        if not df.empty: st.table(df)
        else: st.warning("No 13C-NMR signals detected.")

# --- 4. SUMMARY LOGIC ---
st.divider()
st.info("💡 **Researcher Tip:** Compare the Carbonyl regions across all three tabs for high-confidence structure identification.")
