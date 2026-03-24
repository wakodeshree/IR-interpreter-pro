import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- 1. OFFICIAL MASTER DATABASE ---
OFFICIAL_IR_DATABASE = {
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
    "C-Cl (Halide)": [540, 785, "Strong"]}
# --- STRUCTURE LOGIC ---
STRUCTURE_LOGIC = {
    "All Peaks (No Filter)": [],
    "Aldehyde": ["Aldehyde C=O", "Aldehyde C-H (Fermi)"],
    "Carboxylic Acid": ["Carboxylic Acid C=O", "Carboxylic Acid O-H"],
    "Ester": ["Ester C=O", "C-O Stretch"],
    "Alcohol/Phenol": ["Alcohol O-H", "C-O Stretch"],
    "Ketone": ["Ketone C=O"]
}
target_structure = st.selectbox("Select the expected Structure to verify:", list(STRUCTURE_LOGIC.keys()))
uploaded_file = st.file_uploader("Upload IR Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Verify Structure"):
        with st.spinner("Analyzing graph..."):
            reader = easyocr.Reader(['en'])
            # OCR for Shimadzu vertical labels
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            peaks_found = []
            scale_ignore = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500]
            
            for (bbox, text, prob) in results:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                try:
                    val = float(clean)
                    if int(val) in scale_ignore: continue
                    if 400 <= val <= 4000:
                        for group, r in IR_DB.items():
                            if (r[0]-15) <= val <= (r[1]+15):
                                peaks_found.append({"Wavenumber": val, "Group": group})
                except: continue

            if peaks_found:
                full_df = pd.DataFrame(peaks_found).drop_duplicates(subset=["Wavenumber"])
                req_groups = STRUCTURE_LOGIC[target_structure]
                
                if target_structure == "All Peaks (No Filter)":
                    display_df = full_df
                else:
                    display_df = full_df[full_df["Group"].isin(req_groups)]

                st.subheader(f"✅ Results for: {target_structure}")
                if not display_df.empty:
                    st.table(display_df.sort_values("Wavenumber", ascending=False))
                else:
                    st.error("No peaks found for this specific structure.")
# --- 2. INTERFACE ---
st.set_page_config(page_title="PhD IR Dashboard", layout="wide")
st.title("🔬 Advanced IR Interpretation Engine")
st.write("Full-spectrum analysis based on Table 2.3")

uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Molecular Analysis"):
        with st.spinner("Processing..."):
            reader = easyocr.Reader(['en'])
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            interpretations = []
            for (bbox, text, prob) in results:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I", "1").replace("l", "1")))
                try:
                    val = float(clean)
                    if 400 <= val <= 4000:
                        for group, info in OFFICIAL_IR_DATABASE.items():
                            if (info[0]-12) <= val <= (info[1]+12):
                                interpretations.append({
                                    "Peak Found": val,
                                    "Official Interpretation": group,
                                    "Range": f"{info[0]}-{info[1]}",
                                    "Shape": info[2]
                                })
                except: continue

            if interpretations:
                df = pd.DataFrame(interpretations).drop_duplicates(subset=["Peak Found"]).sort_values("Peak Found", ascending=False)
                
                st.subheader("✅ 1. Detected Peaks & Database Match")
                st.dataframe(df, use_container_width=True)
                
                # --- 3. STRUCTURAL PREDICTION LOGIC ---
                st.subheader("🧪 2. Predicted Structure")
                found = df["Official Interpretation"].tolist()
                
                pred_made = False
                if "Aldehyde (C=O)" in found and "Aldehyde C-H (Fermi)" in found:
                    st.success("🎯 **Structure: ALDEHYDE** (C=O + Fermi Doublet confirmed)")
                    pred_made = True
                elif "Carboxylic Acid (C=O)" in found and "Carboxylic Acid O-H" in found:
                    st.success("🎯 **Structure: CARBOXYLIC ACID** (C=O + Broad O-H confirmed)")
                    pred_made = True
                elif "Ester (C=O)" in found and "C-O Stretch" in found:
                    st.success("🎯 **Structure: ESTER** (C=O + C-O confirmed)")
                    pred_made = True
                
                # Fingerprint Logic
                if "Arom-Mono" in found:
                    st.info("✅ **Aromatic Pattern: Monosubstituted Ring**")
                elif "Arom-Para" in found:
                    st.info("✅ **Aromatic Pattern: Para-disubstituted Ring**")

                if not pred_made:
                    st.info("Molecular fragments identified, but no specific structural match found.")

                # --- 4. DOWNLOAD SECTION ---
                st.divider()
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Analysis Report", data=csv, file_name="IR_Report.csv")
            else:
                st.error("No peaks detected. Ensure labels are clear.")
