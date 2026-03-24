import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- 1. OFFICIAL MASTER DATABASE ---
OFFICIAL_IR_DATABASE = {
    "Alkane C-H (sp3)": [2850, 2970, "Strong"],
    "Alkene C-H (sp2)": [3010, 3100, "Medium"],
    "Aromatic C-H (sp2)": [3000, 3100, "Medium"],
    "Alkyne C-H (sp)": [3260, 3330, "Strong, Sharp"],
    "Aldehyde C-H (Fermi)": [2700, 2850, "Weak, 2 bands"],
    "Nitrile (C≡N)": [2210, 2260, "Medium, Sharp"],
    "Alkyne (C≡C)": [2100, 2260, "Weak/Medium"],
    "Ester (C=O)": [1735, 1750, "Strong"],
    "Aldehyde (C=O)": [1720, 1740, "Strong"],
    "Ketone (C=O)": [1705, 1725, "Strong"],
    "Carboxylic Acid (C=O)": [1700, 1720, "Strong"],
    "Amide (C=O)": [1630, 1690, "Strong"],
    "Alkene (C=C)": [1600, 1680, "Medium"],
    "Aromatic (C=C)": [1450, 1600, "Medium"],
    "Nitro (-NO2)": [1330, 1550, "Strong, Doublet"],
    "Alcohol/Phenol O-H": [3200, 3650, "Strong, Broad"],
    "Carboxylic Acid O-H": [2500, 3300, "Very Broad"],
    "Amine/Amide N-H": [3300, 3500, "Medium"],
    "C-O Stretch": [1000, 1300, "Strong"],
    "Arom-Mono": [690, 770, "Strong (700/750)"],
    "Arom-Para": [800, 860, "Strong (825)"]
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
