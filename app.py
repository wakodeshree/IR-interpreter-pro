import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- WEBSITE CONFIG ---
st.set_page_config(page_title="IR Structure Predictor", layout="wide")
st.title("🔬 IR Structure Predictor Pro")
st.markdown("Automated Peak Detection & Molecular Fragment Prediction")

# --- RESEARCH DATABASE (Table 2.3 Expanded) ---
ir_db = {
    # C-H Region
    "Alkane C-H (stretch)": [2850, 3000, "Strong"],
    "Alkene =C-H (stretch)": [3000, 3100, "Medium"],
    "Aromatic C-H (stretch)": [3010, 3050, "Medium"],
    "Alkyne ≡C-H (stretch)": [3250, 3350, "Strong/Sharp"],
    "Aldehyde (C-H stretch)": [2800, 2900, "Weak/2 peaks"],
    
    # Multiple Bonds
    "Alkene (C=C)": [1600, 1680, "Medium"],
    "Aromatic (C=C)": [1475, 1600, "Medium/Weak"],
    "Alkyne (C≡C)": [2100, 2250, "Medium/Weak"],
    "Nitrile (C≡N)": [2240, 2260, "Medium/Sharp"],

    # Carbonyls (The 1700 Region)
    "Aldehyde C=O": [1720, 1740, "Strong"],
    "Ketone C=O": [1705, 1725, "Strong"],
    "Carboxylic acid C=O": [1700, 1725, "Strong"],
    "Ester C=O": [1730, 1750, "Strong"],
    "Amide C=O": [1630, 1680, "Strong"],
    "Anhydride/Acid Chloride": [1760, 1810, "Strong"],

    # O-H / N-H Region
    "Alcohol O-H (free)": [3600, 3650, "Sharp"],
    "Alcohol O-H (H-bonded)": [3200, 3400, "Strong/Broad"],
    "Carboxylic acid O-H": [2400, 3400, "Very Broad"],
    "Amine/Amide N-H": [3100, 3500, "Medium"],
    
    # Fingerprint/Single Bonds
    "Nitro (-NO2)": [1350, 1550, "Strong"],
    "C-O (Alcohol/Ether/Ester)": [1000, 1300, "Strong"],
    "C-F (Halide)": [1000, 1400, "Strong"],
    "C-Cl (Halide)": [540, 785, "Strong"]
}

uploaded_file = st.file_uploader("Upload IR Graph", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    # --- IMAGE PRE-PROCESSING ---
    raw_img = Image.open(uploaded_file)
    st.image(raw_img, caption="Original Spectrum", use_container_width=True)
    
    # Enhance image for OCR precision
    proc_img = ImageOps.autocontrast(raw_img.convert('L'))
    enhancer = ImageEnhance.Sharpness(proc_img)
    proc_img = enhancer.enhance(2.0)

    if st.button("🚀 Run Molecular Analysis"):
        with st.spinner("Extracting Precise Data..."):
            reader = easyocr.Reader(['en'])
            # rotation_info is critical for vertical Shimadzu labels
            results = reader.readtext(np.array(proc_img), rotation_info=[90, 270])
            
            table_data = []
            for (bbox, text, prob) in results:
                # Cleaning OCR noise while keeping decimals
                clean_text = text.replace("I", "1").replace("l", "1").replace(" ", "")
                clean_text = "".join(re.findall(r'[0-9.]+', clean_text))
                
                try:
                    if len(clean_text) < 3: continue
                    val = float(clean_text)
                    if 400 <= val <= 4000:
                        for group, info in ir_db.items():
                            if (info[0]-12) <= val <= (info[1]+12):
                                table_data.append({"Peak": val, "Group": group, "Intensity": info[2]})
                except: continue

            if table_data:
st.subheader("🧪 Advanced Structural Analysis")

found_peaks = df["Peak"].values
found_groups = df["Group"].values

# 1. SHAPE LOGIC: O-H Broadness Check
if any(3200 <= p <= 3600 for p in found_peaks):
    if any(1700 <= p <= 1750 for p in found_peaks):
        st.info("📢 **Shape Analysis**: Broad O-H + C=O suggests a **Carboxylic Acid Monomer/Dimer**.")
    else:
        st.info("📢 **Shape Analysis**: Strong, Broad O-H suggests a **Polymeric Alcohol**.")

# 2. SUBSTITUTION LOGIC: Aromatic Fingerprinting (675-900 cm-1)
st.subheader("🎯 Aromatic Substitution Pattern")
substitution = "Unknown"

# Monosubstituted: Two strong peaks near 750 and 700
if any(730 <= p <= 770 for p in found_peaks) and any(680 <= p <= 710 for p in found_peaks):
    substitution = "✅ **Monosubstituted Benzene Ring** (Signals at ~750 and ~700 cm⁻¹)"

# Ortho (1,2-Di): One strong peak near 750
elif any(735 <= p <= 770 for p in found_peaks) and not any(680 <= p <= 710 for p in found_peaks):
    substitution = "✅ **Ortho-disubstituted (1,2-di)**"

# Para (1,4-Di): One strong peak near 800-850
elif any(800 <= p <= 860 for p in found_peaks):
    substitution = "✅ **Para-disubstituted (1,4-di)**"

# Meta (1,3-Di): Three peaks (880, 780, 690)
elif any(750 <= p <= 810 for p in found_peaks) and any(680 <= p <= 725 for p in found_peaks):
    substitution = "✅ **Meta-disubstituted (1,3-di)**"

st.success(substitution)
                df = pd.DataFrame(table_data).drop_duplicates(subset=["Peak"]).sort_values("Peak", ascending=False)
                
                st.subheader("1. Identified Peaks")
                st.dataframe(df, use_container_width=True)

                # --- STRUCTURE PREDICTION LOGIC ---
                st.subheader("2. Predicted Molecular Fragments")
                found_groups = df["Group"].values
                found_peaks = df["Peak"].values
                
                predictions = []
                
                # Logic Gate 1: Aldehyde
                if any("C=O" in g for g in found_groups) and any("Aldehyde (C-H)" in g for g in found_groups):
                    predictions.append("✅ **Aldehyde Fragment Detected**: Confirmed by Carbonyl and Fermi Doublet (2720/2820 cm⁻¹).")
                
                # Logic Gate 2: Carboxylic Acid
                elif any("C=O" in g for g in found_groups) and any("Carboxylic Acid (O-H)" in g for g in found_groups):
                    predictions.append("✅ **Carboxylic Acid Detected**: Confirmed by Broad O-H and Strong C=O stretch.")
                
                # Logic Gate 3: Aromatic Ester
                elif any("Ester (C=O)" in g for g in found_groups) and any(1000 <= p <= 1300 for p in found_peaks):
                    predictions.append("✅ **Ester Group Detected**: Confirmed by C=O and C-O stretching pair.")

                # Logic Gate 4: Aromatic System
                if any("Aromatic (C-C)" in g for g in found_groups) or any("Aromatic (C-H)" in g for g in found_groups):
                    predictions.append("✅ **Aromatic Ring Present**: Signature benzene-ring vibrations detected.")

                if predictions:
                    for p in predictions: st.info(p)
                else:
                    st.write("Analysis suggests specific functional groups but requires NMR for full structural assignment.")
                
                # CSV Export
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Analysis CSV", data=csv, file_name="IR_Analysis.csv")
            else:
                st.error("No clear peak labels detected. Ensure the graph has numeric labels above the peaks.")
