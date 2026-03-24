import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- MASTER DATABASES (NO LACKS) ---
IR_DB = {
    "Alcohol/Phenol O-H": [3200, 3650], "Carboxylic Acid O-H": [2400, 3400],
    "Nitrile C≡N": [2240, 2260], "Ester C=O": [1730, 1750], 
    "Aldehyde C=O": [1720, 1740], "Ketone C=O": [1705, 1725],
    "Carboxylic Acid C=O": [1700, 1725], "Amide C=O": [1630, 1680],
    "Nitro (-NO2)": [1350, 1550], "Aromatic C=C": [1475, 1600]
}

H_NMR_DB = {
    "Aldehyde (CHO)": [9.0, 10.0], "Carboxylic Acid (COOH)": [10.5, 13.0],
    "Aromatic (Ar-H)": [6.5, 8.5], "Vinyl (C=CH)": [4.6, 5.9],
    "Alcohol/Ether alpha": [3.3, 4.0], "Alkyl (CH3/CH2)": [0.8, 2.0]
}

C_NMR_DB = {
    "Primary Alkyl (R-CH3)": [8, 35], "Secondary Alkyl (R2CH2)": [15, 50],
    "Tertiary Alkyl (R3CH)": [20, 60], "Quaternary Alkyl (R4C)": [30, 40],
    "Alkyne (C≡C)": [65, 85], "Alkene (C=C)": [100, 150],
    "Aromatic Ring (C)": [110, 170], "Amide/Ester (C=O)": [165, 175],
    "Carboxylic Acid (C=O)": [175, 185], "Aldehyde (C=O)": [190, 200],
    "Ketone (C=O)": [205, 220]
}

# --- SCALE FILTER LOGIC ---
def is_scale_number(val, mode):
    """Checks if a number is likely a graph scale marker"""
    # 1. Scale markers are usually whole integers
    if not (val % 1 == 0): return False 
    
    val_int = int(val)
    if mode == "IR":
        # IR scale markers are usually multiples of 500 or 1000
        return val_int in [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500, 400]
    elif mode == "C-NMR":
        # C-NMR scale markers are usually multiples of 20 or 50
        return val_int % 20 == 0 or val_int % 50 == 0 or val_int in [220, 210, 190, 170]
    elif mode == "H-NMR":
        # H-NMR scale markers are single digits 0 to 12
        return val_int in range(0, 14)
    return False

def process_image(image, mode):
    reader = easyocr.Reader(['en'])
    rot = [90, 270] if mode == "IR" else None
    results = reader.readtext(np.array(image), rotation_info=rot)
    
    final_peaks = []
    for (bbox, text, prob) in results:
        clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
        try:
            val = float(clean)
            # Skip if it's a scale number
            if is_scale_number(val, mode): continue
            
            # Match against Database
            db = IR_DB if mode == "IR" else (H_NMR_DB if mode == "H-NMR" else C_NMR_DB)
            for group, r in db.items():
                # Peaks usually fall within range
                if r[0] <= val <= r[1]:
                    final_peaks.append({"Peak/Shift": val, "Interpretation": group})
        except: continue
        
    return pd.DataFrame(final_peaks).drop_duplicates(subset=["Peak/Shift"]).sort_values("Peak/Shift", ascending=False)

# --- APP INTERFACE ---
st.set_page_config(page_title="PhD Multi-Spec Dashboard", layout="wide")
st.title("🔬 Integrated PhD Multi-Spectral Suite")

tab1, tab2, tab3 = st.tabs(["📡 IR", "🧬 H-NMR", "💎 13C-NMR"])

with tab1:
    f1 = st.file_uploader("Upload IR", type=['png','jpg','jpeg'], key="ir")
    if f1 and st.button("🚀 Analyze IR"):
        df = process_image(Image.open(f1), "IR")
        st.table(df) if not df.empty else st.warning("No Peaks Found")

with tab2:
    f2 = st.file_uploader("Upload H-NMR", type=['png','jpg','jpeg'], key="h")
    if f2 and st.button("🚀 Analyze H-NMR"):
        df = process_image(Image.open(f2), "H-NMR")
        st.table(df) if not df.empty else st.warning("No Signals Found")

with tab3:
    f3 = st.file_uploader("Upload C-NMR", type=['png','jpg','jpeg'], key="c")
    if f3 and st.button("🚀 Analyze 13C-NMR"):
        df = process_image(Image.open(f3), "C-NMR")
        st.table(df) if not df.empty else st.warning("No Signals Found")
