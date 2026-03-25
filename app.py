import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. ENHANCED DATABASE ---
IR_DB = {
    "Alcohol O-H": [3200, 3650], "Carboxylic Acid O-H": [2400, 3400],
    "Aldehyde C-H (Fermi)": [2720, 2850], "Ester C=O": [1730, 1750],
    "Aldehyde C=O": [1720, 1740], "Ketone C=O": [1705, 1725],
    "Carboxylic Acid C=O": [1700, 1725], "Amide C=O": [1630, 1680],
    "Nitro (-NO2)": [1350, 1550], "C-O Stretch": [1000, 1300],
    "Aromatic C=C": [1475, 1600], "Alkane C-H": [2850, 2970]
}

STRUCTURE_LOGIC = {
    "All Peaks (No Filter)": [],
    "Aldehyde": ["Aldehyde C=O", "Aldehyde C-H (Fermi)"],
    "Carboxylic Acid": ["Carboxylic Acid C=O", "Carboxylic Acid O-H"],
    "Ester": ["Ester C=O", "C-O Stretch"],
    "Alcohol/Phenol": ["Alcohol O-H", "C-O Stretch"],
    "Ketone": ["Ketone C=O"]
}

# --- 2. ADVANCED SMART FILTER ---
def smart_spectrum_validation(ocr_results):
    """Detects if the graph is NMR based on keywords and scale ranges"""
    detected_text = " ".join([x[1].lower() for x in ocr_results])
    
    # Check for NMR keywords
    if any(word in detected_text for word in ["ppm", "nmr", "shift", "h-nmr", "c-nmr"]):
        return False, "⚠️ NMR Graph Detected: This app is in IR Mode. Please upload an IR spectrum (cm⁻¹)."

    # Extract all numbers to check the scale
    nums = []
    for x in ocr_results:
        clean = "".join(re.findall(r'[0-9.]+', x[1]))
        if clean:
            try: nums.append(float(clean))
            except: continue
    
    # If the highest number found is very low (e.g., < 250), it's definitely NMR/Carbon
    if nums and max(nums) < 250:
        return False, "⚠️ Scale Error: Peak values are too low for IR. This appears to be an NMR graph."
    
    return True, "Success"

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="PhD IR Smart-Interpreter", layout="wide")
st.title("🔬 Smart-Guard IR Interpreter")
st.markdown("---")

with st.sidebar:
    st.header("📋 Sample Metadata")
    sample_id = st.text_input("Sample ID", "Sample_Ref_01")
    target_structure = st.selectbox("Verify Structure:", list(STRUCTURE_LOGIC.keys()))
    st.divider()
    st.info("Machine Visualization Active: Detecting Graph Type...")

up = st.file_uploader("Upload IR Spectrum", type=['png', 'jpg', 'jpeg'])

if up:
    img = Image.open(up)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Full Analysis"):
        with st.spinner("Machine Scanning..."):
            reader = easyocr.Reader(['en'])
            # We scan the image
            ocr_res = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            # --- STEP 1: SMART VALIDATION ---
            is_valid, message = smart_spectrum_validation(ocr_res)
            
            if not is_valid:
                st.error(message)
            else:
                # --- STEP 2: PROCESS IR DATA ---
                peaks = []
                ignore = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500, 0]
                
                for (bbox, text, prob) in ocr_res:
                    clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                    try:
                        v = float(clean)
                        if int(v) in ignore: continue
                        if 400 <= v <= 4000:
                            for grp, r in IR_DB.items():
                                if r[0]-15 <= v <= r[1]+15:
                                    peaks.append({"Sample": sample_id, "Peak": v, "Group": grp, "Range": f"{r[0]}-{r[1]}"})
                    except: continue

                if peaks:
                    df = pd.DataFrame(peaks).drop_duplicates(subset=["Peak"])
                    
                    # Apply Structural Filter
                    req = STRUCTURE_LOGIC[target_structure]
                    if target_structure != "All Peaks (No Filter)":
                        df = df[df["Group"].isin(req)]
                    
                    st.subheader(f"✅ Analysis for {sample_id}")
                    st.dataframe(df.style.highlight_max(axis=0, subset=['Peak'], color='#3d5a80'))
                    
                    # CSV Download
                    st.download_button("📥 Export CSV", df.to_csv(index=False), f"{sample_id}_IR.csv")
                else:
                    st.warning("No IR peaks detected. Ensure wavenumber labels are clear.")
